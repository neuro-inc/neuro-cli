import asyncio
import logging
import shutil
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any, List, Optional, Sequence, Type, Union, cast

import aiohttp
import click
from aiodocker.exceptions import DockerError
from click.exceptions import Abort as ClickAbort, Exit as ClickExit

import neuromation
from neuromation.api import CONFIG_ENV_NAME, DEFAULT_CONFIG_PATH, ConfigError
from neuromation.cli.root import Root

from . import admin, completion, config, image, job, project, share, storage
from .const import (
    EX_DATAERR,
    EX_IOERR,
    EX_NOPERM,
    EX_OSFILE,
    EX_PLATFORMERROR,
    EX_PROTOCOL,
    EX_SOFTWARE,
    EX_TIMEOUT,
)
from .log_formatter import ConsoleHandler, ConsoleWarningFormatter
from .topics import topics
from .utils import (
    Context,
    DeprecatedGroup,
    MainGroup,
    alias,
    format_example,
    option,
    pager_maybe,
)


if sys.platform == "win32":
    if sys.version_info < (3, 7):
        # Python 3.6 has no WindowsProactorEventLoopPolicy class
        from asyncio import events

        class WindowsProactorEventLoopPolicy(events.BaseDefaultEventLoopPolicy):
            _loop_factory = asyncio.ProactorEventLoop

    else:
        WindowsProactorEventLoopPolicy = asyncio.WindowsProactorEventLoopPolicy

    asyncio.set_event_loop_policy(WindowsProactorEventLoopPolicy())
else:
    if sys.version_info < (3, 8):
        from .asyncio_utils import ThreadedChildWatcher

        asyncio.set_child_watcher(ThreadedChildWatcher())


log = logging.getLogger(__name__)


def setup_logging(verbosity: int, color: bool) -> None:
    root_logger = logging.getLogger()
    handler = ConsoleHandler()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)

    if color:
        format_class: Type[logging.Formatter] = ConsoleWarningFormatter
    else:
        format_class = logging.Formatter

    if verbosity <= 1:
        formatter = format_class()
    else:
        formatter = format_class("%(name)s.%(funcName)s: %(message)s")

    if verbosity < -1:
        loglevel = logging.CRITICAL
    elif verbosity == -1:
        loglevel = logging.ERROR
    elif verbosity == 0:
        loglevel = logging.WARNING
    elif verbosity == 1:
        loglevel = logging.INFO
    else:
        loglevel = logging.DEBUG

    handler.setFormatter(formatter)
    handler.setLevel(loglevel)


LOG_ERROR = log.error


def print_options(
    ctx: click.Context, param: Union[click.Option, click.Parameter], value: Any
) -> Any:
    if not value or ctx.resilient_parsing:
        return

    formatter = ctx.make_formatter()
    formatter.write_text("Options available for any command.")
    EXAMPLE = dedent(
        """\
        # Show config without colors
        neuro --color=no config show
    """
    )
    format_example(EXAMPLE, formatter)

    opts = []
    for parameter in ctx.command.get_params(ctx):
        rv = parameter.get_help_record(ctx)
        if rv is not None:
            opts.append(rv)

    with formatter.section("Options"):
        formatter.write_dl(opts)

    click.echo(formatter.getvalue())
    ctx.exit()


@click.group(cls=MainGroup, invoke_without_command=True)
@option(
    "-v",
    "--verbose",
    count=True,
    type=int,
    default=0,
    help="Give more output. Option is additive, and can be used up to 2 times.",
)
@option(
    "-q",
    "--quiet",
    count=True,
    type=int,
    default=0,
    help="Give less output. Option is additive, and can be used up to 2 times.",
)
@option(
    "--neuromation-config",
    type=click.Path(dir_okay=True, file_okay=False),
    required=False,
    help="Path to config directory.",
    default=DEFAULT_CONFIG_PATH,
    metavar="PATH",
    envvar=CONFIG_ENV_NAME,
)
@option(
    "--show-traceback",
    is_flag=True,
    help="Show python traceback on error, useful for debugging the tool.",
)
@option(
    "--color",
    type=click.Choice(["yes", "no", "auto"]),
    default="auto",
    help="Color mode.",
)
@option(
    "--disable-pypi-version-check",
    is_flag=True,
    help="Don't periodically check PyPI to determine whether a new version of "
    "Neuro Platform CLI is available for download.",
)
@option(
    "--network-timeout", type=float, help="Network read timeout, seconds.", default=60.0
)
@click.version_option(
    version=neuromation.__version__, message="Neuro Platform Client %(version)s"
)
@option(
    "--options",
    is_flag=True,
    callback=print_options,
    expose_value=False,
    is_eager=True,
    hidden=True,
    help="Show common options.",
)
@option(
    "--trace",
    is_flag=True,
    help="Trace sent HTTP requests and received replies to stderr.",
)
@option(
    "--hide-token/--no-hide-token",
    is_flag=True,
    default=None,
    help=(
        "Prevent user's token sent in HTTP headers from being "
        "printed out to stderr during HTTP tracing. Can be used only "
        "together with option '--trace'. On by default."
    ),
)
@option(
    "--skip-stats/--no-skip-stats",
    is_flag=True,
    default=False,
    help=(
        "Skip sending usage statistics to Neuro servers. "
        "Note: the statistics has no sensitive data, e.g. "
        "file, job, image, or user names, executed command lines, "
        "environment variables, etc."
    ),
)
@click.pass_context
def cli(
    ctx: click.Context,
    verbose: int,
    quiet: bool,
    neuromation_config: str,
    show_traceback: bool,
    color: str,
    disable_pypi_version_check: bool,
    network_timeout: float,
    trace: bool,
    hide_token: Optional[bool],
    skip_stats: bool,
) -> None:
    #   ▇ ◣
    #   ▇ ◥ ◣
    # ◣ ◥   ▇
    # ▇ ◣   ▇
    # ▇ ◥ ◣ ▇
    # ▇   ◥ ▇    Neuro Platform
    # ▇   ◣ ◥
    # ◥ ◣ ▇      Deep network training,
    #   ◥ ▇      inference and datasets
    #     ◥
    global LOG_ERROR
    if show_traceback:
        LOG_ERROR = log.exception
    tty = all(f.isatty() for f in [sys.stdin, sys.stdout, sys.stderr])
    COLORS = {"yes": True, "no": False, "auto": None}
    real_color: Optional[bool] = COLORS[color]
    if real_color is None:
        real_color = tty
    ctx.color = real_color
    verbosity = verbose - quiet
    setup_logging(verbosity=verbosity, color=real_color)
    if hide_token is None:
        hide_token_bool = True
    else:
        if not trace:
            option = "--hide-token" if hide_token else "--no-hide-token"
            raise click.UsageError(f"{option} requires --trace")
        hide_token_bool = hide_token
    root = Root(
        verbosity=verbosity,
        color=real_color,
        tty=tty,
        terminal_size=shutil.get_terminal_size(),
        disable_pypi_version_check=disable_pypi_version_check,
        network_timeout=network_timeout,
        config_path=Path(neuromation_config),
        trace=trace,
        trace_hide_token=hide_token_bool,
        command_path="",
        command_params=[],
        skip_gmp_stats=skip_stats,
    )
    ctx.obj = root
    if not ctx.invoked_subcommand:
        click.echo(ctx.get_help())


@cli.command(wrap_async=False)
@click.argument("command", nargs=-1)
@click.pass_context
def help(ctx: click.Context, command: Sequence[str]) -> None:
    """Get help on a command."""
    top_ctx = ctx.find_root()
    root = cast(Root, ctx.obj)

    if len(command) == 1:
        # try to find a topic
        for name, topic in topics.commands.items():
            if name == command[0]:
                # Found a topic
                formatter = ctx.make_formatter()
                topic.format_help_text(top_ctx, formatter)
                pager_maybe(
                    formatter.getvalue().rstrip("\n").splitlines(),
                    root.tty,
                    root.terminal_size,
                )
                return

    not_found = 'No such command "neuro {}"'.format(" ".join(command))

    ctx_stack = [top_ctx]
    for cmd_name in command:
        current_cmd = ctx_stack[-1].command
        if isinstance(current_cmd, click.MultiCommand):
            sub_name, sub_cmd, args = current_cmd.resolve_command(ctx, [cmd_name])
            if sub_cmd is None or sub_cmd.hidden:
                click.echo(not_found)
                break
            sub_ctx = Context(sub_cmd, parent=ctx_stack[-1], info_name=sub_name)
            ctx_stack.append(sub_ctx)
        else:
            click.echo(not_found)
            break
    else:
        help = ctx_stack[-1].get_help()
        pager_maybe(help.splitlines(), root.tty, root.terminal_size)

    for ctx in reversed(ctx_stack[1:]):
        ctx.close()


# groups
cli.add_command(admin.admin)
cli.add_command(job.job)
cli.add_command(project.project)
cli.add_command(storage.storage)
cli.add_command(image.image)
cli.add_command(config.config)
cli.add_command(completion.completion)
cli.add_command(share.acl)

cli.add_command(DeprecatedGroup(storage.storage, name="store", hidden=True))

# shortcuts
cli.add_command(job.run)
cli.add_command(job.submit)
cli.add_command(alias(job.ls, "ps", help=job.ls.help, deprecated=False))
cli.add_command(job.status)
cli.add_command(job.exec)
cli.add_command(job.port_forward)
cli.add_command(job.logs)
cli.add_command(job.kill)
cli.add_command(job.top)
cli.add_command(job.save)
cli.add_command(config.login)
cli.add_command(config.logout)
cli.add_command(storage.cp)
cli.add_command(storage.ls)
cli.add_command(storage.rm)
cli.add_command(storage.mkdir)
cli.add_command(storage.mv)
cli.add_command(alias(image.ls, "images", help=image.ls.help, deprecated=False))
cli.add_command(image.push)
cli.add_command(image.pull)
cli.add_command(alias(share.grant, "share", help=share.grant.help, deprecated=False))

cli.topics = topics  # type: ignore


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
        sys.exit(e.exit_code)  # type: ignore

    except asyncio.TimeoutError:
        LOG_ERROR("Timeout")
        sys.exit(EX_TIMEOUT)

    except neuromation.api.IllegalArgumentError as error:
        LOG_ERROR(f"Illegal argument(s) ({error})")
        sys.exit(EX_DATAERR)

    except neuromation.api.ResourceNotFound as error:
        LOG_ERROR(f"{error}")
        sys.exit(EX_OSFILE)

    except neuromation.api.AuthenticationError as error:
        LOG_ERROR(f"Cannot authenticate ({error})")
        sys.exit(EX_NOPERM)
    except neuromation.api.AuthorizationError as error:
        LOG_ERROR(f"Not enough permissions ({error})")
        sys.exit(EX_NOPERM)

    except neuromation.api.ClientError as error:
        LOG_ERROR(f"Application error ({error})")
        sys.exit(EX_SOFTWARE)

    except neuromation.api.ServerNotAvailable as error:
        LOG_ERROR(f"Application error ({error})")
        sys.exit(EX_PLATFORMERROR)

    except ConfigError as error:
        LOG_ERROR(f"{error}")
        sys.exit(EX_SOFTWARE)

    except aiohttp.ClientError as error:
        LOG_ERROR(f"Connection error ({error})")
        sys.exit(EX_IOERR)

    except DockerError as error:
        LOG_ERROR(f"Docker API error: {error.message}")
        sys.exit(EX_PROTOCOL)

    except NotImplementedError as error:
        LOG_ERROR(f"{error}")
        sys.exit(EX_SOFTWARE)

    except FileNotFoundError as error:
        LOG_ERROR(f"File not found ({error})")
        sys.exit(EX_OSFILE)

    except NotADirectoryError as error:
        LOG_ERROR(f"{error}")
        sys.exit(EX_OSFILE)

    except PermissionError as error:
        LOG_ERROR(f"Cannot access file ({error})")
        sys.exit(EX_NOPERM)

    except OSError as error:
        LOG_ERROR(f"I/O Error ({error})")
        sys.exit(EX_IOERR)

    except KeyboardInterrupt:
        LOG_ERROR("Aborting.")
        sys.exit(130)

    except ValueError as e:
        LOG_ERROR(e)
        sys.exit(127)

    except SystemExit:
        raise

    except Exception as e:
        LOG_ERROR(f"{e}")
        sys.exit(1)
