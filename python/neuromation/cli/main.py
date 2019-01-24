import logging
import os
import sys
from pathlib import Path

import aiohttp
import click
from aiodocker.exceptions import DockerError
from click.exceptions import Abort as ClickAbort, Exit as ClickExit
from yarl import URL

import neuromation
from neuromation.cli.rc import RCException
from neuromation.clientv2 import (
    Action,
    ClientV2,
    Permission,
)
from neuromation.logging import ConsoleWarningFormatter

from . import rc
from .commands import command
from .config import config
from .defaults import DEFAULTS
from .model import model
from .storage import storage
from .job import job
from .utils import Context, DeprecatedGroup, load_token
from .image import image


# For stream copying from file to http or from http to file
BUFFER_SIZE_MB = 16

log = logging.getLogger(__name__)
console_handler = logging.StreamHandler(sys.stderr)


def setup_logging():
    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.DEBUG)

    # Select modules logging, if necessary
    # logging.getLogger("aiohttp.internal").propagate = False
    # logging.getLogger("aiohttp.client").setLevel(logging.DEBUG)


def setup_console_handler(handler, verbose, noansi=False):
    if not handler.stream.closed and handler.stream.isatty() and noansi is False:
        format_class = ConsoleWarningFormatter
    else:
        format_class = logging.Formatter

    if verbose:
        handler.setFormatter(format_class("%(name)s.%(funcName)s: %(message)s"))
        loglevel = logging.DEBUG
    else:
        handler.setFormatter(format_class())
        loglevel = logging.INFO

    handler.setLevel(loglevel)


@command
def neuro(url, token, verbose, show_traceback, version):
    """    ◣
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
Usage:
  neuro [options] COMMAND

Options:
  -u, --url URL         Override API URL [default: {api_url}]
  -t, --token TOKEN     API authentication token (not implemented)
  --verbose             Enable verbose logging
  --show-traceback      Show Python traceback on exception
  -v, --version         Print version and exit

Commands:
  model                 Model training, testing and inference
  job                   Manage existing jobs
  store                 Storage operations
  image                 Docker container image operations
  config                Configure API connection settings
  completion            Generate code to enable completion
  share                 Resource sharing management
  help                  Get help on a command
"""

    @command
    async def share(uri, user, permission: str):
        """
            Usage:
                neuro share URI USER PERMISSION

            Shares resource specified by URI to a USER with PERMISSION \
(read|write|manage)

            Examples:
            neuro share storage:///sample_data/ alice manage
            neuro share image://{username}/resnet50 bob read
            neuro share image:resnet50 bob read
            neuro share job:///my_job_id alice write
        """
        uri = URL(uri)
        try:
            action = Action[permission.upper()]
        except KeyError as error:
            raise ValueError(
                "Resource not shared. Please specify one of read/write/manage."
            ) from error
        config = rc.ConfigFactory.load()
        platform_user_name = config.get_platform_user_name()
        permission = Permission.from_cli(
            username=platform_user_name, uri=uri, action=action
        )

        async with ClientV2(url, token) as client:
            try:
                await client.users.share(user, permission)
            except neuromation.client.IllegalArgumentError as error:
                raise ValueError(
                    "Resource not shared. Please verify resource-uri, user name."
                ) from error
        return "Resource shared."

    @command
    def completion():
        """
            Usage:
                neuro completion COMMAND

            Generates code to enable bash-completion.

            Commands:
                generate     Generate code enabling bash-completion.
                             eval $(neuro completion generate) enables completion
                             for the current session.
                             Adding eval $(neuro completion generate) to
                             .bashrc_profile enables completion permanently.
                patch        Automatically patch .bash_profile to enable completion
        """
        neuromation_dir = Path(__file__).parent.parent
        completion_file = neuromation_dir / "completion" / "completion.bash"
        activate_completion = "source '{}'".format(str(completion_file))

        @command
        def generate():
            """
               Usage:
                   neuro completion generate

               Generate code enabling bash-completion.
               eval $(neuro completion generate) enables completion for the current
               session.
               Adding eval $(neuro completion generate) to .bashrc_profile enables
               completion permanently.
            """
            print(activate_completion)

        @command
        def patch():
            """
               Usage:
                   neuro completion patch

               Automatically patch .bash_profile to enable completion
            """
            bash_profile_file = Path.home() / ".bash_profile"
            with bash_profile_file.open("a+") as bash_profile:
                bash_profile.write(activate_completion)
                bash_profile.write("\n")

        return locals()

    @command
    def help():
        """
            Usage:
                neuro help COMMAND [SUBCOMMAND[...]]

            Display help for given COMMAND

            Examples:
                neuro help store
                neuro help store ls

        """
        pass

    return locals()


LOG_ERROR = log.error


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("-v", "--verbose", count=True, type=int)
@click.option("--show-traceback", is_flag=True)
@click.option("-u", "--url", default=DEFAULTS["api_url"])
@click.option("-t", "--token", default=load_token)
@click.version_option(
    version=neuromation.__version__, message="Neuromation Platform Client %(version)s"
)
@click.pass_context
def cli(
    ctx: click.Context, verbose: int, show_traceback: bool, token: str, url: str
) -> None:
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
    ctx.obj = Context(token=token, url=URL(url))


@cli.command()
def help():
    """Get help on a command"""


cli.add_command(config)
cli.add_command(storage)
cli.add_command(DeprecatedGroup(storage, name="store"))
cli.add_command(model)
cli.add_command(job)
cli.add_command(image)


def main():
    try:
        cli.main(standalone_mode=False)
    except ClickAbort:
        LOG_ERROR("Aborting.")
        sys.exit(130)
    except click.ClickException as e:
        e.show()
        sys.exit(e.exit_code)
    except ClickExit as e:
        sys.exit(e.exit_code)
    except neuromation.clientv2.IllegalArgumentError as error:
        LOG_ERROR(f"Illegal argument(s) ({error})")
        sys.exit(os.EX_DATAERR)

    except neuromation.clientv2.ResourceNotFound as error:
        LOG_ERROR(f"{error}")
        sys.exit(os.EX_OSFILE)

    except neuromation.clientv2.AuthenticationError as error:
        LOG_ERROR(f"Cannot authenticate ({error})")
        sys.exit(os.EX_NOPERM)
    except neuromation.clientv2.AuthorizationError as error:
        LOG_ERROR(f"You haven`t enough permission ({error})")
        sys.exit(os.EX_NOPERM)

    except neuromation.clientv2.ClientError as error:
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
