import asyncio
import dataclasses
import functools
import inspect
import itertools
import logging
import re
import shlex
import sys
import time
from contextlib import suppress
from datetime import date, timedelta
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

import certifi
import click
import humanize
import pkg_resources
from click import BadParameter
from yarl import URL

import neuromation
from neuromation.api import (
    Action,
    Client,
    Factory,
    JobDescription,
    LocalImage,
    RemoteImage,
    TagOption,
    Volume,
)
from neuromation.api.config import _CookieSession, _PyPIVersion
from neuromation.api.parsing_utils import _ImageNameParser
from neuromation.api.url_utils import _normalize_uri, uri_from_cli

from .asyncio_utils import run
from .parse_utils import JobColumnInfo, parse_columns, to_megabytes
from .root import Root
from .stats import upload_gmp_stats
from .version_utils import AbstractVersionChecker, DummyVersionChecker, VersionChecker


log = logging.getLogger(__name__)

_T = TypeVar("_T")

DEPRECATED_HELP_NOTICE = " " + click.style("(DEPRECATED)", fg="red")
DEPRECATED_INVOKE_NOTICE = "DeprecationWarning: The command {name} is deprecated."

# NOTE: these job name defaults are taken from `platform_api` file `validators.py`
JOB_NAME_MIN_LENGTH = 3
JOB_NAME_MAX_LENGTH = 40
JOB_NAME_PATTERN = "^[a-z](?:-?[a-z0-9])*$"
JOB_NAME_REGEX = re.compile(JOB_NAME_PATTERN)


def warn_if_has_newer_version(
    version: _PyPIVersion,
    check_neuromation: bool = True,
    cerfiti_warning_delay_days: int = 14,
) -> None:
    if check_neuromation:
        current = pkg_resources.parse_version(neuromation.__version__)
        if current < version.pypi_version:
            update_command = "pip install --upgrade neuromation"
            click.secho(
                f"You are using Neuro Platform Client {current}, "
                f"however {version.pypi_version} is available.\n"
                f"You should consider upgrading via "
                f"the '{update_command}' command.",
                err=True,
                fg="yellow",
            )

    certifi_current = pkg_resources.parse_version(certifi.__version__)  # type: ignore

    if certifi_current < version.certifi_pypi_version and _need_to_warn_after_delay(
        version.certifi_pypi_upload_date, cerfiti_warning_delay_days
    ):
        pip_update_command = "pip install --upgrade certifi"
        conda_update_command = "conda update certifi"
        click.secho(
            f"Your root certificates are out of date.\n"
            f"You are using certifi {certifi_current}, "
            f"however {version.certifi_pypi_version} is available.\n"
            f"Please consider upgrading certifi package, e.g.\n"
            f"    {pip_update_command}\n"
            f"or\n"
            f"    {conda_update_command}",
            err=True,
            fg="red",
        )


def _need_to_warn_after_delay(release_date: date, delay_days: int) -> bool:
    warn_since = date.today() - timedelta(days=delay_days)
    return release_date < warn_since


async def _run_async_function(
    init_client: bool,
    func: Callable[..., Awaitable[_T]],
    root: Root,
    *args: Any,
    **kwargs: Any,
) -> _T:
    loop = asyncio.get_event_loop()
    version_checker: AbstractVersionChecker

    if init_client:
        await root.init_client()

        version = root._config.pypi

        warn_if_has_newer_version(version, not root.disable_pypi_version_check)

        if root.disable_pypi_version_check:
            version_checker = DummyVersionChecker(version)
        else:
            # (ASvetlov) This branch is not tested intentionally
            # Don't want to fetch PyPI from unit tests
            # Later the checker initialization code will be refactored
            # as a part of config reimplementation
            version_checker = VersionChecker(version)  # pragma: no cover
        pypi_task: Optional["asyncio.Task[None]"] = loop.create_task(
            version_checker.run()
        )
        stats_task: "asyncio.Task[None]" = loop.create_task(
            upload_gmp_stats(
                root.client, root.command_path, root.command_params, root.skip_gmp_stats
            )
        )
    else:
        pypi_task = None
        stats_task = loop.create_task(asyncio.sleep(0))  # do nothing

    try:
        return await func(root, *args, **kwargs)
    finally:
        with suppress(asyncio.CancelledError):
            await stats_task
        new_config = None
        if pypi_task is not None:
            pypi_task.cancel()
            with suppress(asyncio.CancelledError):
                await pypi_task
            with suppress(asyncio.CancelledError):
                await version_checker.close()

            if version_checker.version != root._config.pypi:
                # Update pypi section
                new_config = dataclasses.replace(
                    root._config, pypi=version_checker.version
                )

        cookie = root.get_session_cookie()
        if cookie is not None:
            if new_config is None:
                new_config = root._config
            new_config = dataclasses.replace(
                new_config,
                cookie_session=_CookieSession(
                    cookie=cookie.value, timestamp=int(time.time())
                ),
            )

        if new_config is not None:
            factory = root._factory
            assert factory is not None
            factory._save(new_config)

        await root.close()

        # looks ugly but proper fix requires aiohttp changes
        if sys.platform == "win32":
            # Windows need a longer sleep
            await asyncio.sleep(0.2)
        else:
            await asyncio.sleep(0.1)


def _wrap_async_callback(
    callback: Callable[..., Awaitable[_T]], init_client: bool = True,
) -> Callable[..., _T]:
    assert inspect.iscoroutinefunction(callback)
    # N.B. the decorator implies @click.pass_obj
    @click.pass_obj
    @functools.wraps(callback)
    def wrapper(root: Root, *args: Any, **kwargs: Any) -> _T:
        return run(
            _run_async_function(init_client, callback, root, *args, **kwargs),
            debug=root.verbosity >= 2,  # see main:setup_logging for constants
        )

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


def split_examples(help: str) -> List[str]:
    return re.split("Example[s]:\n", help, re.IGNORECASE)


def format_example(example: str, formatter: click.HelpFormatter) -> None:
    with formatter.section(click.style("Examples", bold=True, underline=False)):
        for line in example.splitlines():
            is_comment = line.startswith("#")
            if is_comment:
                formatter.write_text("\b\n" + click.style(line, dim=True))
            else:
                formatter.write_text("\b\n" + " ".join(shlex.split(line)))


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
            help_text, *examples = split_examples(help)
            if help_text:
                formatter.write_paragraph()
                with formatter.indentation():
                    if deprecated:
                        help_text += DEPRECATED_HELP_NOTICE
                    formatter.write_text(help_text)
            examples = [example.strip() for example in examples]

            for example in examples:
                format_example(example, formatter)
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


class NeuroGroupMixin(NeuroClickMixin):
    def format_options(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        self.format_commands(ctx, formatter)  # type: ignore


def _collect_params(cmd: click.Command, ctx: click.Context) -> Dict[str, Optional[str]]:
    params = ctx.params.copy()
    for param in cmd.get_params(ctx):
        if param.name not in params:
            continue
        if params[param.name] == param.get_default(ctx):
            # drop default param
            del params[param.name]
            continue
        if param.param_type_name != "option":
            # save name only
            params[param.name] = None
        else:
            if getattr(param, "secure", True):
                params[param.name] = None
            else:
                params[param.name] = str(params[param.name])
    return params


class Command(NeuroClickMixin, click.Command):
    def __init__(
        self,
        callback: Any,
        init_client: bool = True,
        wrap_async: bool = True,
        **kwargs: Any,
    ) -> None:
        if wrap_async:
            callback = _wrap_async_callback(callback, init_client=init_client)
        super().__init__(
            callback=callback, **kwargs,
        )

    def invoke(self, ctx: click.Context) -> Any:
        """Given a context, this invokes the attached callback (if it exists)
        in the right way.
        """
        if self.deprecated:
            click.echo(
                click.style(DEPRECATED_INVOKE_NOTICE.format(name=self.name), fg="red"),
                err=True,
            )
        if self.callback is not None:
            # init_client=init_client,
            # ctx.parent.params
            # breakpoint()
            ctx2 = ctx
            params = [_collect_params(ctx2.command, ctx2)]
            while ctx2.parent:
                ctx2 = ctx2.parent
                params.append(_collect_params(ctx2.command, ctx2))
            params.reverse()
            root = cast(Root, ctx.obj)
            root.command_path = ctx.command_path
            root.command_params = params
            return ctx.invoke(self.callback, **ctx.params)


def command(
    name: Optional[str] = None, cls: Type[Command] = Command, **kwargs: Any
) -> Command:
    return click.command(name=name, cls=cls, **kwargs)  # type: ignore


class Group(NeuroGroupMixin, click.Group):
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


class DeprecatedGroup(NeuroGroupMixin, click.MultiCommand):
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
    topics = None

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
            help = cmd.get_short_help_str(limit)
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
        topics: List[Tuple[str, click.Command]] = []
        if self.topics is not None:
            topics = list(self.topics.commands.items())

        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            # What is this, the tool lied about a command.  Ignore it
            if cmd is None:
                continue
            if cmd.hidden:
                continue

            if isinstance(cmd, click.MultiCommand):
                groups.append((subcommand, cmd))
            else:
                commands.append((subcommand, cmd))

        self._format_group("Commands", groups, formatter)
        self._format_group("Command Shortcuts", commands, formatter)
        self._format_group("Help topics", topics, formatter)

    def format_options(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        self.format_commands(ctx, formatter)
        formatter.write_paragraph()
        formatter.write_text(
            'Use "neuro help <command>" for more information '
            "about a given command or topic."
        )
        formatter.write_text(
            'Use "neuro --options" for a list of global command-line options '
            "(applies to all commands)."
        )


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
        hidden = origin.hidden

    return Command(
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
        wrap_async=False,
    )


class Option(click.Option):
    def __init__(self, *args: Any, secure: bool = False, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.secure = secure


def option(*param_decls: Any, **attrs: Any) -> Callable[..., Any]:
    option_attrs = attrs.copy()
    option_attrs.setdefault("cls", Option)
    return click.option(*param_decls, **option_attrs)


def volume_to_verbose_str(volume: Volume) -> str:
    return (
        f"'{volume.storage_uri}' mounted to '{volume.container_path}' "
        f"in {('ro' if volume.read_only else 'rw')} mode"
    )


async def resolve_job(id_or_name_or_uri: str, *, client: Client) -> str:
    default_user = client.username
    if id_or_name_or_uri.startswith("job:"):
        uri = _normalize_uri(id_or_name_or_uri, username=default_user)
        id_or_name = uri.path.lstrip("/")
        owner = uri.host or default_user
        if not id_or_name:
            raise ValueError(
                f"Invalid job URI: owner='{owner}', missing job-id or job-name"
            )
    else:
        id_or_name = id_or_name_or_uri
        owner = default_user

    jobs: List[JobDescription] = []
    details = f"name={id_or_name}, owner={owner}"
    try:
        jobs = await client.jobs.list(name=id_or_name, owners={owner})
    except Exception as e:
        log.error(
            f"Failed to resolve job-name {id_or_name_or_uri} resolved as "
            f"{details} to a job-ID: {e}"
        )
    if jobs:
        job_id = jobs[-1].id
        log.debug(f"Job name '{id_or_name}' resolved to job ID '{job_id}'")
    else:
        job_id = id_or_name

    return job_id


SHARE_SCHEMES = ("storage", "image", "job")


def parse_resource_for_sharing(uri: str, root: Root) -> URL:
    """ Parses the neuromation resource URI string.
    Available schemes: storage, image, job. For image URIs, tags are not allowed.
    """
    if uri.startswith("image:"):
        image = root.client.parse.remote_image(uri, tag_option=TagOption.DENY)
        uri = str(image)

    return uri_from_cli(
        uri, root.client.username, allowed_schemes=("storage", "image", "job")
    )


def parse_file_resource(uri: str, root: Root) -> URL:
    """ Parses the neuromation resource URI string.
    Available schemes: file, storage.
    """
    return uri_from_cli(uri, root.client.username, allowed_schemes=("file", "storage"))


def parse_permission_action(action: str) -> Action:
    try:
        return Action[action.upper()]
    except KeyError:
        valid_actions = ", ".join([a.value for a in Action])
        raise ValueError(
            f"invalid permission action '{action}', allowed values: {valid_actions}"
        )


class LocalImageType(click.ParamType):
    name = "local_image"

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> LocalImage:
        assert ctx is not None
        root = cast(Root, ctx.obj)
        config = Factory(root.config_path)._read()
        image_parser = _ImageNameParser(
            config.auth_token.username,
            config.clusters[config.cluster_name].registry_url,
        )
        if image_parser.is_in_neuro_registry(value):
            raise click.BadParameter(
                "remote image cannot be used as local", ctx, param, self.name
            )
        else:
            parsed_image = image_parser.parse_as_local_image(value)
        return parsed_image


class ImageType(click.ParamType):
    name = "image"

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> RemoteImage:
        assert ctx is not None
        root = cast(Root, ctx.obj)
        config = Factory(root.config_path)._read()
        image_parser = _ImageNameParser(
            config.auth_token.username,
            config.clusters[config.cluster_name].registry_url,
        )
        return image_parser.parse_remote(value)


class RemoteTaglessImageType(click.ParamType):
    name = "image"

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> RemoteImage:
        assert ctx is not None
        root = cast(Root, ctx.obj)
        config = Factory(root.config_path)._read()
        image_parser = _ImageNameParser(
            config.auth_token.username,
            config.clusters[config.cluster_name].registry_url,
        )
        return image_parser.parse_as_neuro_image(value, tag_option=TagOption.DENY)


class LocalRemotePortParamType(click.ParamType):
    name = "local-remote-port-pair"

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> Tuple[int, int]:
        try:
            local_str, remote_str = value.split(":")
            local, remote = int(local_str), int(remote_str)
            if not (0 < local <= 65535 and 0 < remote <= 65535):
                raise ValueError("Port should be in range 1 to 65535")
            return local, remote
        except ValueError as e:
            raise BadParameter(f"{value} is not a valid port combination: {e}")


LOCAL_REMOTE_PORT = LocalRemotePortParamType()


class MegabyteType(click.ParamType):
    name = "megabyte"

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> int:
        return to_megabytes(value)


MEGABYTE = MegabyteType()


class JobNameType(click.ParamType):
    name = "job_name"

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> str:
        if (
            len(value) < JOB_NAME_MIN_LENGTH
            or len(value) > JOB_NAME_MAX_LENGTH
            or JOB_NAME_REGEX.match(value) is None
        ):
            raise ValueError(
                f"Invalid job name '{value}'.\n"
                "The name can only contain lowercase letters, numbers and hyphens "
                "with the following rules: \n"
                "  - the first character must be a letter; \n"
                "  - each hyphen must be surrounded by non-hyphen characters; \n"
                f"  - total length must be between {JOB_NAME_MIN_LENGTH} and "
                f"{JOB_NAME_MAX_LENGTH} characters long."
            )
        return value


JOB_NAME = JobNameType()


class JobColumnsType(click.ParamType):
    name = "columns"

    def convert(
        self,
        value: Union[str, List[JobColumnInfo]],
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> List[JobColumnInfo]:
        if isinstance(value, list):
            return value
        return parse_columns(value)


JOB_COLUMNS = JobColumnsType()


def do_deprecated_quiet(
    ctx: click.Context, param: Union[click.Option, click.Parameter], value: Any
) -> Any:
    if value and not ctx.obj.quiet:
        ctx.obj.verbosity = -2
        click.echo(
            click.style(
                "DeprecationWarning: "
                "The local option --quiet is deprecated. "
                "Use global option --quiet instead.",
                fg="red",
            ),
            err=True,
        )
        # Patch the logger as it was set up with verbosity=-2.
        root_logger = logging.getLogger()
        handler = root_logger.handlers[-1]
        assert handler.formatter
        format_class = type(handler.formatter)
        handler.setFormatter(format_class())
        handler.setLevel(logging.ERROR)


deprecated_quiet_option: Any = option(
    "-q",
    "--quiet",
    is_flag=True,
    callback=do_deprecated_quiet,
    help="Run command in quiet mode (DEPRECATED)",
    expose_value=False,
    is_eager=True,
)


if sys.version_info >= (3, 7):  # pragma: no cover
    from contextlib import AsyncExitStack  # noqa
else:
    from async_exit_stack import AsyncExitStack  # noqa


def format_size(value: float) -> str:
    return humanize.naturalsize(value, gnu=True, format="%.4g")


def pager_maybe(
    lines: Iterable[str], tty: bool, terminal_size: Tuple[int, int]
) -> None:
    if not tty:
        for line in lines:
            click.echo(line)
        return

    lines_it: Iterator[str] = iter(lines)
    count = int(terminal_size[1] * 2 / 3)
    handled = list(itertools.islice(lines_it, count))
    if len(handled) < count:
        # lines list is short, just print it
        for line in handled:
            click.echo(line)
    else:
        click.echo_via_pager(
            itertools.chain(["\n".join(handled)], (f"\n{line}" for line in lines_it))
        )
