import asyncio
import logging
import shutil
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any, List, Optional, Sequence, Type, Union

import aiohttp
import click
from aiodocker.exceptions import DockerError
from click.exceptions import Abort as ClickAbort, Exit as ClickExit

import neuromation
from neuromation.api import CONFIG_ENV_NAME, DEFAULT_CONFIG_PATH, ConfigError
from neuromation.cli.root import Root

from . import completion, config, image, job, share, storage
from .const import EX_DATAERR, EX_IOERR, EX_NOPERM, EX_OSFILE, EX_PROTOCOL, EX_SOFTWARE
from .log_formatter import ConsoleHandler, ConsoleWarningFormatter
from .utils import Context, DeprecatedGroup, MainGroup, alias, format_example


if sys.platform == "win32":
    if sys.version_info < (3, 7):
        # Python 3.6 has no WindowsProactorEventLoopPolicy class
        from asyncio import events

        class WindowsProactorEventLoopPolicy(events.BaseDefaultEventLoopPolicy):
            _loop_factory = asyncio.ProactorEventLoop

    else:
        WindowsProactorEventLoopPolicy = asyncio.WindowsProactorEventLoopPolicy

    asyncio.set_event_loop_policy(WindowsProactorEventLoopPolicy())


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
@click.option(
    "-v",
    "--verbose",
    count=True,
    type=int,
    default=0,
    help="Give more output. Option is additive, and can be used up to 2 times.",
)
@click.option(
    "-q",
    "--quiet",
    count=True,
    type=int,
    default=0,
    help="Give less output. Option is additive, and can be used up to 2 times.",
)
@click.option(
    "--neuromation-config",
    type=click.Path(dir_okay=False),
    required=False,
    help="Path to config file.",
    default=DEFAULT_CONFIG_PATH,
    metavar="PATH",
    envvar=CONFIG_ENV_NAME,
)
@click.option(
    "--show-traceback",
    is_flag=True,
    help="Show python traceback on error, useful for debugging the tool.",
)
@click.option(
    "--color",
    type=click.Choice(["yes", "no", "auto"]),
    default="auto",
    help="Color mode.",
)
@click.option(
    "--disable-pypi-version-check",
    is_flag=True,
    help="Don't periodically check PyPI to determine whether a new version of "
    "Neuromation CLI is available for download.",
)
@click.option(
    "--network-timeout", type=float, help="Network read timeout, seconds.", default=60.0
)
@click.version_option(
    version=neuromation.__version__, message="Neuromation Platform Client %(version)s"
)
@click.option(
    "--options",
    is_flag=True,
    callback=print_options,
    expose_value=False,
    is_eager=True,
    hidden=True,
    help="Show common options.",
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
) -> None:
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
    tty = all(f.isatty() for f in [sys.stdin, sys.stdout, sys.stderr])
    COLORS = {"yes": True, "no": False, "auto": None}
    real_color: Optional[bool] = COLORS[color]
    if real_color is None:
        real_color = tty
    ctx.color = real_color
    verbosity = verbose - quiet
    setup_logging(verbosity=verbosity, color=real_color)
    root = Root(
        verbosity=verbosity,
        color=real_color,
        tty=tty,
        terminal_size=shutil.get_terminal_size(),
        disable_pypi_version_check=disable_pypi_version_check,
        network_timeout=network_timeout,
        config_path=Path(neuromation_config),
    )
    ctx.obj = root
    if not ctx.invoked_subcommand:
        click.echo(ctx.get_help())


@cli.command()
@click.argument("command", nargs=-1)
@click.pass_context
def help(ctx: click.Context, command: Sequence[str]) -> None:
    """Get help on a command."""
    top_ctx = ctx.find_root()

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
        click.echo(help)

    for ctx in reversed(ctx_stack[1:]):
        ctx.close()


# groups
cli.add_command(job.job)
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
