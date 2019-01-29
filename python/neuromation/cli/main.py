import logging
import os
import sys
from typing import List, Optional, Sequence, Type

import aiohttp
import click
from aiodocker.exceptions import DockerError
from click.exceptions import Abort as ClickAbort, Exit as ClickExit  # type: ignore

import neuromation
from neuromation.cli.rc import RCException
from neuromation.logging import ConsoleWarningFormatter

from . import rc
from .completion import completion
from .config import config, login, logout
from .image import image
from .job import job
from .model import model
from .share import share
from .storage import storage
from .utils import DeprecatedGroup


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


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("-v", "--verbose", count=True, type=int)
@click.option("--show-traceback", is_flag=True)
@click.version_option(
    version=neuromation.__version__, message="Neuromation Platform Client %(version)s"
)
@click.pass_context
def cli(ctx: click.Context, verbose: int, show_traceback: bool) -> None:
    """
    \b
       ▇ ◣
       ▇ ◥ ◣
     ◣ ◥   ▇
     ▇ ◣   ▇
     ▇ ◥ ◣ ▇
     ▇   ◥ ▇    Neuromation Platform
     ▇   ◣ ◥
     ◥ ◣ ▇      Deep network training,
       ◥ ▇      inference and datasets
         ◥
    """
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
    """Get help on a command"""
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


cli.add_command(login)
cli.add_command(logout)
cli.add_command(config)
cli.add_command(storage)
cli.add_command(DeprecatedGroup(storage, name="store"))
cli.add_command(model)
cli.add_command(job)
cli.add_command(image)
cli.add_command(share)
cli.add_command(completion)


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
