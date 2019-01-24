import logging
import os
import shlex
import sys
from pathlib import Path

import aiohttp
import click
from aiodocker.exceptions import DockerError
from click.exceptions import Abort as ClickAbort, Exit as ClickExit
from yarl import URL

import neuromation
from neuromation.cli.formatter import JobStatusFormatter, OutputFormatter
from neuromation.cli.rc import Config, RCException
from neuromation.clientv2 import (
    Action,
    ClientV2,
    Image,
    NetworkPortForwarding,
    Permission,
    Resources,
    Volume,
)
from neuromation.logging import ConsoleWarningFormatter
from neuromation.strings.parse import to_megabytes_str

from . import rc
from .command_spinner import SpinnerBase
from .commands import command
from .config import config
from .defaults import DEFAULTS
from .formatter import JobListFormatter
from .model import model
from .ssh_utils import connect_ssh
from .storage import storage
from .utils import Context, DeprecatedGroup, load_token


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
    def image():
        """
        Usage:
            neuro image COMMAND

        Docker image operations

        Commands:
          push                 Push docker image from local machine to cloud registry.
          pull                 Pull docker image from cloud registry to local machine.
          ls                   List available user's images.
        """

        @command
        async def push(image_name, remote_image_name):
            """
            Usage:
                neuro image push IMAGE_NAME [REMOTE_IMAGE_NAME]

            Push an image to platform registry.
            Remote image must be URL with image:// scheme.
            Image names can contains tag. If tags not specified 'latest' will \
be used as value.

            Examples:
                neuro image push myimage
                neuro image push alpine:latest image:my-alpine:production
                neuro image push alpine image://myfriend/alpine:shared

            """
            from neuromation.clientv2.images import Image

            config: Config = rc.ConfigFactory.load()
            username = config.get_platform_user_name()

            local_image = remote_image = Image.from_local(image_name, username)
            if remote_image_name:
                remote_image = Image.from_url(URL(remote_image_name), username)

            spinner = SpinnerBase.create_spinner(
                sys.stdout.isatty(), "Pushing image {}  "
            )

            async with ClientV2(url, token) as client:
                result_remote_image = await client.images.push(
                    local_image, remote_image, spinner
                )
                print(result_remote_image.url)

        @command
        async def pull(image_name, local_image_name):
            """
            Usage:
                neuro image pull IMAGE_NAME [LOCAL_IMAGE_NAME]

            Pull an image from platform registry.
            Remote image name must be URL with image:// scheme.
            Image names can contain tag.

            Examples:
                neuro image pull image:myimage
                neuro image pull image://myfriend/alpine:shared
                neuro image pull image://{username}/my-alpine:production \
alpine:from-registry

            """

            from neuromation.clientv2.images import Image

            config: Config = rc.ConfigFactory.load()
            username = config.get_platform_user_name()

            remote_image = local_image = Image.from_url(URL(image_name), username)
            if local_image_name:
                local_image = Image.from_local(local_image_name, username)

            spinner = SpinnerBase.create_spinner(
                sys.stdout.isatty(), "Pulling image {}  "
            )

            async with ClientV2(url, token) as client:
                result_local_image = await client.images.pull(
                    remote_image, local_image, spinner
                )
                print(result_local_image.local)

        @command
        async def ls():
            """
            Usage:
                neuro image ls

            List user's images which are available for jobs.
            You will see here own and shared with you images
            """

            async with ClientV2(url, token) as client:
                images = await client.images.ls()
                for image in images:
                    print(f"{image}")

        return locals()

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
