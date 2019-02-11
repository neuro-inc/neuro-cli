import asyncio
import re
import shlex
from functools import wraps
from typing import (
    Any,
    Awaitable,
    Callable,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
)

import click

from neuromation.client import Volume
from neuromation.utils import run

from .version_utils import VersionChecker


_T = TypeVar("_T")

DEPRECATED_HELP_NOTICE = " " + click.style("(DEPRECATED)", fg="red")


async def _run_async_function(
    func: Callable[..., Awaitable[_T]], *args: Any, **kwargs: Any
) -> _T:
    loop = asyncio.get_event_loop()
    version_checker = VersionChecker()
    loop.create_task(version_checker.run())
    return await func(*args, **kwargs)


def run_async(callback: Callable[..., Awaitable[_T]]) -> Callable[..., _T]:
    @wraps(callback)
    def wrapper(*args: Any, **kwargs: Any) -> _T:
        return run(_run_async_function(callback, *args, **kwargs))

    return wrapper


class HelpFormatter(click.HelpFormatter):
    def write_usage(self, prog: str, args: str = "", prefix: str = "Usage:") -> None:
        super().write_usage(prog, args, prefix=click.style(prefix, bold=True) + " ")

    def write_heading(self, heading: str) -> None:
        self.write(
            click.style(
                "%*s%s:\n" % (self.current_indent, "", heading),
                bold=True,
                underline=False,
            )
        )


class Context(click.Context):
    def make_formatter(self) -> click.HelpFormatter:
        return HelpFormatter(
            width=self.terminal_width, max_width=self.max_content_width
        )


class NeuroClickMixin:
    def get_short_help_str(self, limit: int = 45) -> str:
        text = super().get_short_help_str(limit=limit)  # type: ignore
        if text.endswith(".") and not text.endswith("..."):
            text = text[:-1]
        return text

    def format_help_text(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        """Writes the help text to the formatter if it exists."""
        help = self.help  # type: ignore
        deprecated = self.deprecated  # type: ignore
        if help:
            help_text, *examples = re.split("Example[s]:\n", help, re.IGNORECASE)
            formatter.write_paragraph()
            with formatter.indentation():
                if deprecated:
                    help_text += DEPRECATED_HELP_NOTICE
                formatter.write_text(help_text)
            examples = [example.strip() for example in examples]

            for example in examples:
                with formatter.section(
                    click.style("Examples", bold=True, underline=False)
                ):
                    for line in example.splitlines():
                        is_comment = line.startswith("#")
                        if is_comment:
                            formatter.write_text("\b\n" + click.style(line, dim=True))
                        else:
                            formatter.write_text("\b\n" + " ".join(shlex.split(line)))
        elif deprecated:
            formatter.write_paragraph()
            with formatter.indentation():
                formatter.write_text(DEPRECATED_HELP_NOTICE)

    def make_context(
        self,
        info_name: str,
        args: Sequence[str],
        parent: Optional[click.Context] = None,
        **extra: Any,
    ) -> Context:
        for key, value in self.context_settings.items():  # type: ignore
            if key not in extra:
                extra[key] = value
        ctx = Context(self, info_name=info_name, parent=parent, **extra)  # type: ignore
        with ctx.scope(cleanup=False):
            self.parse_args(ctx, args)  # type: ignore
        return ctx


class Command(NeuroClickMixin, click.Command):
    pass


def command(
    name: Optional[str] = None, cls: Type[Command] = Command, **kwargs: Any
) -> Command:
    return click.command(name=name, cls=cls, **kwargs)  # type: ignore


class Group(NeuroClickMixin, click.Group):
    def command(
        self, *args: Any, **kwargs: Any
    ) -> Callable[[Callable[..., Any]], Command]:
        def decorator(f: Callable[..., Any]) -> Command:
            cmd = command(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd

        return decorator

    def group(
        self, *args: Any, **kwargs: Any
    ) -> Callable[[Callable[..., Any]], "Group"]:
        def decorator(f: Callable[..., Any]) -> Group:
            cmd = group(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd

        return decorator

    def list_commands(self, ctx: click.Context) -> Iterable[str]:
        return self.commands


def group(name: Optional[str] = None, **kwargs: Any) -> Group:
    kwargs.setdefault("cls", Group)
    return click.group(name=name, **kwargs)  # type: ignore


class DeprecatedGroup(NeuroClickMixin, click.MultiCommand):
    def __init__(
        self, origin: click.MultiCommand, name: Optional[str] = None, **attrs: Any
    ) -> None:
        attrs.setdefault("help", f"Alias for {origin.name}")
        attrs.setdefault("deprecated", True)
        super().__init__(name, **attrs)
        self.origin = origin

    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[click.Command]:
        return self.origin.get_command(ctx, cmd_name)

    def list_commands(self, ctx: click.Context) -> Iterable[str]:
        return self.origin.list_commands(ctx)


class MainGroup(Group):
    def _format_group(
        self,
        title: str,
        grp: Sequence[Tuple[str, click.Command]],
        formatter: click.HelpFormatter,
    ) -> None:
        # allow for 3 times the default spacing
        if not grp:
            return

        width = formatter.width
        assert width is not None
        limit = width - 6 - max(len(cmd[0]) for cmd in grp)

        rows = []
        for subcommand, cmd in grp:
            help = cmd.get_short_help_str(limit)  # type: ignore
            rows.append((subcommand, help))

        if rows:
            with formatter.section(title):
                formatter.write_dl(rows)

    def format_commands(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        """Extra format methods for multi methods that adds all the commands
        after the options.
        """
        commands: List[Tuple[str, click.Command]] = []
        groups: List[Tuple[str, click.MultiCommand]] = []

        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            # What is this, the tool lied about a command.  Ignore it
            if cmd is None:
                continue
            if cmd.hidden:  # type: ignore
                continue

            if isinstance(cmd, click.MultiCommand):
                groups.append((subcommand, cmd))
            else:
                commands.append((subcommand, cmd))

        self._format_group("Command Groups", groups, formatter)
        self._format_group("Commands", commands, formatter)


def alias(
    origin: click.Command,
    name: str,
    *,
    deprecated: bool = True,
    hidden: Optional[bool] = None,
    help: Optional[str] = None,
) -> click.Command:
    if help is None:
        help = f"Alias for {origin.name}."
    if hidden is None:
        hidden = origin.hidden  # type: ignore

    return Command(  # type: ignore
        name=name,
        context_settings=origin.context_settings,
        callback=origin.callback,
        params=origin.params,
        help=help,
        epilog=origin.epilog,
        short_help=origin.short_help,
        options_metavar=origin.options_metavar,
        add_help_option=origin.add_help_option,
        hidden=hidden,
        deprecated=deprecated,
    )


def volume_to_verbose_str(volume: Volume) -> str:
    return (
        f"'{volume.storage_path}' mounted to '{volume.container_path}' "
        f"in {('ro' if volume.read_only else 'rw')} mode"
    )
