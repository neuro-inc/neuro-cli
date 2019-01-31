import logging
import os
import sys
from typing import Any, List, Optional, Sequence, Tuple, Type

import aiohttp
import click
from aiodocker.exceptions import DockerError
from click.exceptions import Abort as ClickAbort, Exit as ClickExit  # type: ignore

import neuromation
from neuromation.cli.rc import RCException
from neuromation.logging import ConsoleWarningFormatter

from . import completion, config, image, job, model, rc, share, storage
from .utils import DeprecatedGroup, alias


# For stream copying from file to http or from http to file
BUFFER_SIZE_MB = 16

log = logging.getLogger(__name__)
console_handler = logging.StreamHandler(sys.stderr)


def setup_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.DEBUG)

    # Select modules logging, if necessary
    # logging.getLogger("aiohttp.internal").propagate = False
    # logging.getLogger("aiohttp.client").setLevel(logging.DEBUG)


def setup_console_handler(
    handler: logging.StreamHandler, verbose: int, noansi: bool = False
) -> None:
    if not handler.stream.closed and handler.stream.isatty() and noansi is False:
        format_class: Type[logging.Formatter] = ConsoleWarningFormatter
    else:
        format_class = logging.Formatter

    if verbose:
        handler.setFormatter(format_class("%(name)s.%(funcName)s: %(message)s"))
        loglevel = logging.DEBUG
    else:
        handler.setFormatter(format_class())
        loglevel = logging.INFO

    handler.setLevel(loglevel)


LOG_ERROR = log.error


class HelpFormatter(click.HelpFormatter):
    def write_heading(self, heading: str) -> None:
        self.write(
            click.style(
                "%*s%s:\n" % (self.current_indent, "", heading),
                bold=True,
                underline=True,
            )
        )


class Context(click.Context):
    def make_formatter(self):
        return HelpFormatter(
            width=self.terminal_width, max_width=self.max_content_width
        )


class MainGroup(click.Group):
    def make_context(
        self,
        info_name: str,
        args: Sequence[str],
        parent: Optional[click.Context] = None,
        **extra: Any,
    ) -> Context:
        for key, value in self.context_settings.items():
            if key not in extra:
                extra[key] = value
        ctx = Context(self, info_name=info_name, parent=parent, **extra)
        with ctx.scope(cleanup=False):
            self.parse_args(ctx, args)
        return ctx

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


@click.group(cls=MainGroup)
@click.option("-v", "--verbose", count=True, type=int)
@click.option("--show-traceback", is_flag=True)
@click.version_option(
    version=neuromation.__version__, message="Neuromation Platform Client %(version)s"
)
@click.pass_context
def cli(ctx: click.Context, verbose: int, show_traceback: bool) -> None:
    """
    Neuromation console.
    """
    #   ▇ ◣
    #   ▇ ◥ ◣
    # ◣ ◥   ▇
    # ▇ ◣   ▇
    # ▇ ◥ ◣ ▇
    # ▇   ◥ ▇    Neuromation Platform
    # ▇   ◣ ◥
    # ◥ ◣ ▇      Deep network training,
    #   ◥ ▇      inference and datasets
    #     ◥
    global LOG_ERROR
    if show_traceback:
        LOG_ERROR = log.exception
    setup_logging()
    setup_console_handler(console_handler, verbose=verbose)
    config = rc.ConfigFactory.load()
    ctx.obj = config


@cli.command()
@click.argument("command", nargs=-1)
@click.pass_context
def help(ctx: click.Context, command: Sequence[str]) -> None:
    """Get help on a command."""
    top_ctx = ctx
    while top_ctx.parent is not None:
        top_ctx = top_ctx.parent

    not_found = 'No such command neuro "{}"'.format(" ".join(command))

    ctx_stack = [top_ctx]
    for cmd_name in command:
        current_cmd = ctx_stack[-1].command
        if isinstance(current_cmd, click.MultiCommand):
            sub_name, sub_cmd, args = current_cmd.resolve_command(ctx, [cmd_name])
            if sub_cmd is None:
                click.echo(not_found)
                break
            sub_ctx = click.Context(sub_cmd, parent=ctx_stack[-1], info_name=sub_name)
            ctx_stack.append(sub_ctx)
        else:
            click.echo(not_found)
            break
    else:
        help = ctx_stack[-1].get_help()
        click.echo(help)

    for ctx in reversed(ctx_stack[1:]):
        ctx.close()


cli.add_command(config.config)
cli.add_command(config.login)
cli.add_command(config.logout)
cli.add_command(storage.storage)
cli.add_command(storage.rm)
cli.add_command(storage.ls)
cli.add_command(storage.cp)
cli.add_command(storage.mkdir)
cli.add_command(storage.mv)
cli.add_command(DeprecatedGroup(storage.storage, name="store"))
cli.add_command(model.model)
cli.add_command(job.job)
cli.add_command(job.submit)
cli.add_command(job.exec)
cli.add_command(job.logs)
cli.add_command(alias(job.ls, "ps", help=job.ls.help, deprecated=False))
cli.add_command(job.status)
cli.add_command(job.top)
cli.add_command(job.kill)
cli.add_command(image.image)
cli.add_command(image.push)
cli.add_command(image.pull)
cli.add_command(alias(image.ls, "images", help=image.ls.help, deprecated=False))
cli.add_command(share.share)
cli.add_command(completion.completion)


def main(args: Optional[List[str]] = None) -> None:
    try:
        cli.main(args=args, standalone_mode=False)
    except ClickAbort:
        LOG_ERROR("Aborting.")
        sys.exit(130)
    except click.ClickException as e:
        e.show()
        sys.exit(e.exit_code)
    except ClickExit as e:
        sys.exit(e.exit_code)
    except neuromation.client.IllegalArgumentError as error:
        LOG_ERROR(f"Illegal argument(s) ({error})")
        sys.exit(os.EX_DATAERR)

    except neuromation.client.ResourceNotFound as error:
        LOG_ERROR(f"{error}")
        sys.exit(os.EX_OSFILE)

    except neuromation.client.AuthenticationError as error:
        LOG_ERROR(f"Cannot authenticate ({error})")
        sys.exit(os.EX_NOPERM)
    except neuromation.client.AuthorizationError as error:
        LOG_ERROR(f"You haven`t enough permission ({error})")
        sys.exit(os.EX_NOPERM)

    except neuromation.client.ClientError as error:
        LOG_ERROR(f"Application error ({error})")
        sys.exit(os.EX_SOFTWARE)

    except RCException as error:
        LOG_ERROR(f"{error}")
        sys.exit(os.EX_SOFTWARE)

    except aiohttp.ClientError as error:
        LOG_ERROR(f"Connection error ({error})")
        sys.exit(os.EX_IOERR)

    except DockerError as error:
        LOG_ERROR(f"Docker API error: {error.message}")
        sys.exit(os.EX_PROTOCOL)

    except NotImplementedError as error:
        LOG_ERROR(f"{error}")
        sys.exit(os.EX_SOFTWARE)
    except FileNotFoundError as error:
        LOG_ERROR(f"File not found ({error})")
        sys.exit(os.EX_OSFILE)
    except NotADirectoryError as error:
        LOG_ERROR(f"{error}")
        sys.exit(os.EX_OSFILE)
    except PermissionError as error:
        LOG_ERROR(f"Cannot access file ({error})")
        sys.exit(os.EX_NOPERM)
    except OSError as error:
        LOG_ERROR(f"I/O Error ({error})")
        sys.exit(os.EX_IOERR)

    except KeyboardInterrupt:
        LOG_ERROR("Aborting.")
        sys.exit(130)
    except ValueError as e:
        print(e)
        sys.exit(127)
    except SystemExit:
        raise
    except Exception as e:
        LOG_ERROR(f"{e}")
        sys.exit(1)
