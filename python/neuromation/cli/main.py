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
    def job():
        """
        Usage:
            neuro job COMMAND

        Model operations

        Commands:
          submit              Starts Job on a platform
          monitor             Monitor job output stream
          list                List all jobs
          status              Display status of a job
          kill                Kill job
          ssh                 Start SSH terminal
          exec                Execute command in a running job
        """

        @command
        async def submit(
            image,
            gpu,
            gpu_model,
            cpu,
            memory,
            extshm,
            http,
            ssh,
            cmd,
            volume,
            env,
            env_file,
            preemptible,
            non_preemptible,
            description,
            quiet,
        ):
            """
            Usage:
                neuro job submit [options] [--volume MOUNT]...
                      [--env VAR=VAL]... IMAGE [CMD...]

            Start job using IMAGE

            COMMANDS list will be passed as commands to model container.

            Options:
                -g, --gpu NUMBER          Number of GPUs to request \
[default: {job_submit_gpu_number}]
                --gpu-model MODEL         GPU to use [default: {job_submit_gpu_model}]
                                          Other options available are
                                              nvidia-tesla-k80
                                              nvidia-tesla-p4
                                              nvidia-tesla-v100
                -c, --cpu NUMBER          Number of CPUs to request \
[default: {job_submit_cpu_number}]
                -m, --memory AMOUNT       Memory amount to request \
[default: {job_submit_memory_amount}]
                -x, --extshm              Request extended '/dev/shm' space
                --http NUMBER             Enable HTTP port forwarding to container
                --ssh NUMBER              Enable SSH port forwarding to container
                --volume MOUNT...         Mounts directory from vault into container
                                          Use multiple options to mount more than one \
volume
                -e, --env VAR=VAL...      Set environment variable in container
                                          Use multiple options to define more than one \
variable
                --env-file FILE           File with environment variables to pass
                --preemptible             Force job to run on a preemptible instance
                --non-preemptible         Force job to run on a non-preemptible instance
                -d, --description DESC    Add optional description to the job
                -q, --quiet               Run command in quiet mode (print only job id)


            Examples:
            # Starts a container pytorch:latest with two paths mounted. Directory /q1/
            # is mounted in read only mode to /qm directory within container.
            # Directory /mod mounted to /mod directory in read-write mode.
            neuro job submit --volume storage:/q1:/qm:ro --volume storage:/mod:/mod:rw \
pytorch:latest

            # Starts a container pytorch:latest with connection enabled to port 22 and
            # sets PYTHONPATH environment value to /python.
            # Please note that SSH server should be provided by container.
            neuro job submit --env PYTHONPATH=/python --volume \
storage:/data/2018q1:/data:ro --ssh 22 pytorch:latest
            """

            def get_preemptible():  # pragma: no cover
                if preemptible and non_preemptible:
                    raise neuromation.client.IllegalArgumentError(
                        "Incompatible options: --preemptible and --non-preemptible"
                    )
                return preemptible or not non_preemptible  # preemptible by default

            is_preemptible = get_preemptible()

            config: Config = rc.ConfigFactory.load()
            username = config.get_platform_user_name()

            # TODO (Alex Davydow 12.12.2018): Consider splitting env logic into
            # separate function.
            if env_file:
                with open(env_file, "r") as ef:
                    env = ef.read().splitlines() + env

            env_dict = {}
            for line in env:
                splited = line.split("=", 1)
                if len(splited) == 1:
                    val = os.environ.get(splited[0], "")
                    env_dict[splited[0]] = val
                else:
                    env_dict[splited[0]] = splited[1]

            cmd = " ".join(cmd) if cmd is not None else None
            log.debug(f'cmd="{cmd}"')

            memory = to_megabytes_str(memory)
            image = Image(image=image, command=cmd)
            network = NetworkPortForwarding.from_cli(http, ssh)
            resources = Resources.create(cpu, gpu, gpu_model, memory, extshm)
            volumes = Volume.from_cli_list(username, volume)

            async with ClientV2(url, token) as client:
                job = await client.jobs.submit(
                    image=image,
                    resources=resources,
                    network=network,
                    volumes=volumes,
                    is_preemptible=is_preemptible,
                    description=description,
                    env=env_dict,
                )
                return OutputFormatter.format_job(job, quiet)

        @command
        async def exec(id, tty, no_key_check, cmd):
            """
            Usage:
                neuro job exec [options] ID CMD...

            Executes command in a running job.

            Options:
                -t, --tty         Allocate virtual tty. Useful for interactive jobs.
                --no-key-check    Disable host key checks. Should be used with caution.
            """
            cmd = shlex.split(" ".join(cmd))
            async with ClientV2(url, token) as client:
                retcode = await client.jobs.exec(id, tty, no_key_check, cmd)
            sys.exit(retcode)

        @command
        async def ssh(id, user, key):
            """
            Usage:
                neuro job ssh [options] ID

            Starts ssh terminal connected to running job.
            Job should be started with SSH support enabled.

            Options:
                --user STRING         Container user name [default: {job_ssh_user}]
                --key STRING          Path to container private key.

            Examples:
            neuro job ssh --user alfa --key ./my_docker_id_rsa job-abc-def-ghk
            """
            config: Config = rc.ConfigFactory.load()
            git_key = config.github_rsa_path

            async with ClientV2(url, token) as client:
                await connect_ssh(client, id, git_key, user, key)

        @command
        async def monitor(id):
            """
            Usage:
                neuro job monitor ID

            Monitor job output stream
            """
            timeout = aiohttp.ClientTimeout(
                total=None, connect=None, sock_read=None, sock_connect=30
            )

            async with ClientV2(url, token, timeout=timeout) as client:
                async for chunk in client.jobs.monitor(id):
                    if not chunk:
                        break
                    sys.stdout.write(chunk.decode(errors="ignore"))

        @command
        async def list(status, description, quiet):
            """
            Usage:
                neuro job list [options]

            Options:
              -s, --status (pending|running|succeeded|failed|all)
                  Filter out job by status(es) (comma delimited if multiple)
              -d, --description DESCRIPTION
                  Filter out job by job description (exact match)
              -q, --quiet
                  Run command in quiet mode (print only job ids)

            List all jobs

            Examples:
            neuro job list --description="my favourite job"
            neuro job list --status=all
            neuro job list --status=pending,running --quiet
            """

            status = status or "running,pending"

            # TODO: add validation of status values
            statuses = set(status.split(","))
            if "all" in statuses:
                statuses = set()

            async with ClientV2(url, token) as client:
                jobs = await client.jobs.list()

            formatter = JobListFormatter(quiet=quiet)
            return formatter.format_jobs(jobs, statuses, description)

        @command
        async def status(id):
            """
            Usage:
                neuro job status ID

            Display status of a job
            """
            async with ClientV2(url, token) as client:
                res = await client.jobs.status(id)
                return JobStatusFormatter.format_job_status(res)

        @command
        async def kill(job_ids):
            """
            Usage:
                neuro job kill JOB_IDS...

            Kill job(s)
            """
            errors = []
            async with ClientV2(url, token) as client:
                for job in job_ids:
                    try:
                        await client.jobs.kill(job)
                        print(job)
                    except ValueError as e:
                        errors.append((job, e))

            def format_fail(job: str, reason: Exception) -> str:
                return f"Cannot kill job {job}: {reason}"

            for job, error in errors:
                print(format_fail(job, error))

        return locals()

    @command
    def image():
        """
        Usage:
            neuro image COMMAND

        Docker image operations

        Commands:
          push                 Push docker image from local machine to cloud registry.
          pull                 Pull docker image from cloud registry to local machine.
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
                result_remote_image = await client.images.pull(
                    local_image, remote_image, spinner
                )
                print(result_remote_image.url)

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
