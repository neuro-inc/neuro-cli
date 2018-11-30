import logging
import os
import sys
from functools import partial
from pathlib import Path
from typing import Union
from urllib.parse import urlparse

import aiohttp

import neuromation
from neuromation.cli.command_handlers import (
    CopyOperation,
    DockerHandler,
    JobHandlerOperations,
    ModelHandlerOperations,
    PlatformListDirOperation,
    PlatformMakeDirOperation,
    PlatformRemoveOperation,
    PlatformRenameOperation,
    PlatformSharingOperations,
)
from neuromation.cli.formatter import JobStatusFormatter, OutputFormatter
from neuromation.cli.rc import Config
from neuromation.client.client import TimeoutSettings
from neuromation.client.jobs import ResourceSharing
from neuromation.logging import ConsoleWarningFormatter

from . import rc
from .commands import command, dispatch


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
def neuro(url, token, verbose, version):
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

    from neuromation.client import Storage

    @command
    def config():
        """
        Usage:
            neuro config COMMAND

        Client configuration settings commands

        Settings:
            url             Updates API URL
            auth            Updates API Token
            forget          Forget stored API Token
            id_rsa          Updates path to Github RSA token,
                            in use for SSH/Remote debug
            show            Print current settings
        """

        @command
        def url(url):
            """
            Usage:
                neuro config url URL

            Updates settings with provided platform URL.

            Example:
            neuro config url http://platform.neuromation.io/api/v1
            """
            rc.ConfigFactory.update_api_url(url)

        @command
        def id_rsa(file):
            """
            Usage:
                neuro config id_rsa FILE

            Updates path to id_rsa file with private key.
            File is being used for accessing remote shell, remote debug.

            Note: this is temporal and going to be
            replaced in future by JWT token.
            """
            if not os.path.exists(file) or not os.path.isfile(file):
                print(f"File does not exist id_rsa={file}.")
                return

            rc.ConfigFactory.update_github_rsa_path(file)

        @command
        def show():
            """
            Usage:
                neuro config show

            Prints current settings.
            """
            config = rc.ConfigFactory.load()
            print(config)

        @command
        def auth(token):
            """
            Usage:
                neuro config auth TOKEN

            Updates authorization token
            """
            # TODO (R Zubairov, 09/13/2018): check token correct
            # connectivity, check with Alex
            # Do not overwrite token in case new one does not work
            # TODO (R Zubairov, 09/13/2018): on server side we shall implement
            # protection against brute-force
            rc.ConfigFactory.update_auth_token(token=token)

        @command
        def forget():
            """
            Usage:
                neuro config forget

            Forget authorization token
            """
            rc.ConfigFactory.forget_auth_token()

        return locals()

    @command
    def store():
        """
        Usage:
            neuro store COMMAND

        Storage operations

        Commands:
          rm                 Remove files or directories
          ls                 List directory contents
          cp                 Copy files and directories
          mv                 Move or rename files and directories
          mkdir              Make directories
        """

        storage = partial(Storage, url, token)

        @command
        def rm(path):
            """
            Usage:
                neuro store rm PATH

            Remove files or directories.

            Example:
            neuro store rm storage:///foo/bar/
            neuro store rm storage:/foo/bar/
            neuro store rm storage://{username}/foo/bar/
            """
            config = rc.ConfigFactory.load()
            platform_user_name = config.get_platform_user_name()
            PlatformRemoveOperation(platform_user_name).remove(path, storage)

        @command
        def ls(path):
            """
            Usage:
                neuro store ls [PATH]

            List directory contents
            By default PATH is equal user`s home dir (storage:)
            """
            if path is None:
                path = "storage:"

            format = "{type:<15}{size:<15,}{name:<}".format

            config = rc.ConfigFactory.load()
            platform_user_name = config.get_platform_user_name()
            ls_op = PlatformListDirOperation(platform_user_name)
            storage_objects = ls_op.ls(path, storage)

            print(
                "\n".join(
                    format(type=status.type.lower(), name=status.path, size=status.size)
                    for status in storage_objects
                )
            )

        @command
        def cp(source, destination, recursive, progress):
            """
            Usage:
                neuro store cp [options] SOURCE DESTINATION

            Copy files and directories
            Either SOURCE or DESTINATION should have storage:// scheme.
            If scheme is omitted, file:// scheme is assumed.

            Options:
              -r, --recursive             Recursive copy
              -p, --progress              Show progress

            Example:

            # copy local file ./foo into remote storage root
            neuro store cp ./foo storage:///
            neuro store cp ./foo storage:/

            # download remote file foo into local file foo with
            # explicit file:// scheme set
            neuro store cp storage:///foo file:///foo
            """
            timeout = TimeoutSettings(
                total=None, connect=None, sock_read=None, sock_connect=30
            )
            storage = partial(Storage, url, token, timeout)
            src = urlparse(source, scheme="file")
            dst = urlparse(destination, scheme="file")

            log.debug(f"src={src}")
            log.debug(f"dst={dst}")

            config = rc.ConfigFactory.load()
            platform_user_name = config.get_platform_user_name()
            operation = CopyOperation.create(
                platform_user_name, src.scheme, dst.scheme, recursive, progress
            )

            if operation:
                return operation.copy(src, dst, storage)

            raise neuromation.client.IllegalArgumentError(
                "Invalid SOURCE or DESTINATION value"
            )

        @command
        def mkdir(path):
            """
            Usage:
                neuro store mkdir PATH

            Make directories
            """
            config = rc.ConfigFactory.load()
            platform_user_name = config.get_platform_user_name()
            PlatformMakeDirOperation(platform_user_name).mkdir(path, storage)
            return path

        @command
        def mv(source, destination):
            """
            Usage:
                neuro store mv SOURCE DESTINATION

            Move or rename files and directories. SOURCE must contain path to the
            file or directory existing on the storage, and DESTINATION must contain
            the full path to the target file or directory.


            Example:

            # move or rename remote file
            neuro store mv storage://{username}/foo.txt storage://{username}/bar.txt
            neuro store mv storage://{username}/foo.txt storage://~/bar/baz/foo.txt

            # move or rename remote directory
            neuro store mv storage://{username}/foo/ storage://{username}/bar/
            neuro store mv storage://{username}/foo/ storage://{username}/bar/baz/foo/
            """
            config = rc.ConfigFactory.load()
            platform_user_name = config.get_platform_user_name()
            operation = PlatformRenameOperation(platform_user_name)
            return operation.mv(source, destination, storage)

        return locals()

    @command
    def model():
        """
        Usage:
            neuro model COMMAND

        Model operations

        Commands:
          train              Start model training
          test               Test trained model against validation dataset
          infer              Start batch inference
          debug              Prepare debug tunnel for PyCharm
        """

        from neuromation.client.jobs import Model
        from neuromation.client.jobs import Job

        jobs = partial(Job, url, token)
        model = partial(Model, url, token)

        @command
        def train(
            image,
            dataset,
            results,
            gpu,
            gpu_model,
            cpu,
            memory,
            extshm,
            http,
            ssh,
            cmd,
            description,
            quiet,
        ):
            """
            Usage:
                neuro model train [options] IMAGE DATASET RESULTS [CMD...]

            Start training job using model from IMAGE, dataset from DATASET and
            store output weights in RESULTS.

            COMMANDS list will be passed as commands to model container.

            Options:
                -g, --gpu NUMBER          Number of GPUs to request [default: 1]
                --gpu-model MODEL         GPU to use [default: nvidia-tesla-k80]
                                          Other options available are
                                              nvidia-tesla-p4, nvidia-tesla-v100.
                -c, --cpu NUMBER          Number of CPUs to request [default: 1.0]
                -m, --memory AMOUNT       Memory amount to request [default: 16G]
                -x, --extshm              Request extended '/dev/shm' space
                --http NUMBER             Enable HTTP port forwarding to container
                --ssh NUMBER              Enable SSH port forwarding to container
                -d, --description DESC    Add optional description to the job
                -q, --quiet               Run command in quiet mode (print only job id)
            """

            config: Config = rc.ConfigFactory.load()
            platform_user_name = config.get_platform_user_name()
            model_operation = ModelHandlerOperations(platform_user_name)
            job = model_operation.train(
                image,
                dataset,
                results,
                gpu,
                gpu_model,
                cpu,
                memory,
                extshm,
                cmd,
                model,
                http,
                ssh,
                description,
            )

            return OutputFormatter.format_job(job, quiet)

        @command
        def debug(id, localport):
            """
            Usage:
                neuro model debug [options] ID

            Starts ssh terminal connected to running job.
            Job should be started with SSH support enabled.

            Options:
                --localport NUMBER    Local port number for debug [default: 31234]

            Example:
            neuro model debug --localport 12789 job-abc-def-ghk
            """
            config: Config = rc.ConfigFactory.load()
            git_key = config.github_rsa_path
            platform_user_name = config.get_platform_user_name()

            JobHandlerOperations(platform_user_name).python_remote_debug(
                id, git_key, localport, jobs
            )
            return None

        @command
        def test():
            pass

        @command
        def infer():
            pass

        return locals()

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
        """

        from neuromation.client.jobs import Job

        jobs = partial(Job, url, token)

        @command
        def submit(
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
            preemptible,
            description,
            quiet,
        ):
            """
            Usage:
                neuro job submit [options] [--volume MOUNT]... IMAGE [CMD...]

            Start job using IMAGE

            COMMANDS list will be passed as commands to model container.

            Options:
                -g, --gpu NUMBER          Number of GPUs to request [default: 1]
                --gpu-model MODEL         GPU to use [default: nvidia-tesla-k80]
                                          Other options available are
                                              nvidia-tesla-p4, nvidia-tesla-v100.
                -c, --cpu NUMBER          Number of CPUs to request [default: 1.0]
                -m, --memory AMOUNT       Memory amount to request [default: 16G]
                -x, --extshm              Request extended '/dev/shm' space
                --http NUMBER             Enable HTTP port forwarding to container
                --ssh NUMBER              Enable SSH port forwarding to container
                --volume MOUNT...         Mounts directory from vault into container
                --preemptible             Run job on a lower-cost preemptible instance
                -d, --description DESC    Add optional description to the job
                -q, --quiet               Run command in quiet mode


            Examples:
            neuro job submit --volume storage:/q1:/qm:ro --volume storage:/mod:/mod:rw
                pytorch:latest

            Starts a container pytorch:latest with two paths mounted. Directory
            /q1/ is mounter in read only mode to /qm directory
            within container. Directory /mod mounted to /mod
            directory in read-write mode.

            neuro job submit  --volume storage:/data/2018q1:/data:ro --ssh 22
               pytorch:latest

            Starts a container pytorch:latest with connection enabled to port 22.
            Please note that SSH server should be provided by container.
            """

            config: Config = rc.ConfigFactory.load()
            platform_user_name = config.get_platform_user_name()

            job = JobHandlerOperations(platform_user_name).submit(
                image,
                gpu,
                gpu_model,
                cpu,
                memory,
                extshm,
                cmd,
                http,
                ssh,
                volume,
                jobs,
                preemptible,
                description,
            )
            return OutputFormatter.format_job(job, quiet)

        @command
        def ssh(id, user, key):
            """
            Usage:
                neuro job ssh [options] ID

            Starts ssh terminal connected to running job.
            Job should be started with SSH support enabled.

            Options:
                --user STRING         Container user name [default: root]
                --key STRING          Path to container private key.

            Example:
            neuro job ssh --user alfa --key ./my_docker_id_rsa job-abc-def-ghk
            """
            config: Config = rc.ConfigFactory.load()
            git_key = config.github_rsa_path
            platform_user_name = config.get_platform_user_name()

            JobHandlerOperations(platform_user_name).connect_ssh(
                id, git_key, user, key, jobs
            )
            return None

        @command
        def monitor(id):
            """
            Usage:
                neuro job monitor ID

            Monitor job output stream
            """
            timeout = TimeoutSettings(
                total=None, connect=None, sock_read=None, sock_connect=30
            )
            jobs = partial(Job, url, token, timeout)

            with jobs() as j:
                with j.monitor(id) as stream:
                    while True:
                        chunk = stream.read()
                        if not chunk:
                            break
                        sys.stdout.write(chunk.decode(errors="ignore"))

        @command
        def list(status, description, quiet):
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

            Example:
            neuro job list --description="my favourite job"
            neuro job list --status=all
            neuro job list --status=pending,running --quiet
            """

            status = status or "running,pending"
            # TODO (Artem Yushkovskiy, 29.11.2018): add validation of status values
            return JobHandlerOperations(token).list_jobs(
                jobs, status, quiet, description
            )

        @command
        def status(id):
            """
            Usage:
                neuro job status ID

            Display status of a job
            """
            res = JobHandlerOperations(token).status(id, jobs)
            return JobStatusFormatter.format_job_status(res)

        @command
        def kill(job_ids):
            """
            Usage:
                neuro job kill JOB_IDS...

            Kill job(s)
            """
            already_deads, errors = [], []
            with jobs() as j:
                for job in job_ids:
                    try:
                        error = j.kill(job)
                        if error is None:  # success
                            print(job)
                        else:
                            already_deads.append((job, error))
                    except ValueError as e:
                        errors.append((job, e))

            def format_fail(job: str, reason: Union[str, Exception]) -> str:
                return f"Cannot kill job {job}: {reason}"

            for job, reason in already_deads:
                print(format_fail(job, reason))
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

        def _get_image_platform_full_name(image_name):
            config = rc.ConfigFactory.load()
            registry_url = config.docker_registry_url()
            user_name = config.get_platform_user_name()
            target_image_name = f"{registry_url}/{user_name}/{image_name}"
            return target_image_name

        @command
        def push(image_name):
            """
            Usage:
                neuro image push IMAGE_NAME

            Push an image to platform registry
            """
            config = rc.ConfigFactory.load()
            platform_user_name = config.get_platform_user_name()
            registry_url = config.docker_registry_url()
            return DockerHandler(platform_user_name, config.auth).push(
                registry_url, image_name
            )

        @command
        def pull(image_name):
            """
            Usage:
                neuro image pull IMAGE_NAME

            Pull an image from platform registry
            """
            config = rc.ConfigFactory.load()
            platform_user_name = config.get_platform_user_name()
            registry_url = config.docker_registry_url()
            return DockerHandler(platform_user_name, config.auth).pull(
                registry_url, image_name
            )

        return locals()

    @command
    def share(uri, whom, read, write, manage):
        """
            Usage:
                neuro share URI WHOM (read|write|manage)

            Shares resource specified by URI to a user specified by WHOM
             allowing to read, write or manage it.

            Example:
            neuro share storage:///sample_data/ alice manage
            neuro share image:///resnet50 bob read
            neuro share job:///my_job_id alice write
        """

        op_type = "manage" if manage else "write" if write else "read" if read else None
        if not op_type:
            print("Resource not shared. " "Please specify one of read/write/manage.")
            return None

        config = rc.ConfigFactory.load()
        platform_user_name = config.get_platform_user_name()

        try:
            resource_sharing = partial(ResourceSharing, url, token)
            share_command = PlatformSharingOperations(platform_user_name)
            share_command.share(uri, op_type, whom, resource_sharing)
        except neuromation.client.IllegalArgumentError:
            print("Resource not shared. " "Please verify resource-uri, user name.")
            return None
        print("Resource shared.")
        return None

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

    return locals()


def main():
    setup_logging()
    setup_console_handler(console_handler, verbose=("--verbose" in sys.argv))

    version = f"Neuromation Platform Client {neuromation.__version__}"
    if "-v" in sys.argv:
        print(version)
        sys.exit(0)

    config = rc.ConfigFactory.load()
    doc_username = config.get_platform_user_name()
    if not doc_username:
        doc_username = "username"
    format_spec = {"api_url": config.url, "username": doc_username}

    try:
        res = dispatch(
            target=neuro, tail=sys.argv[1:], format_spec=format_spec, token=config.auth
        )
        if res:
            print(res)

    except neuromation.client.IllegalArgumentError as error:
        log.error(f"Illegal argument(s) ({error})")
        sys.exit(os.EX_DATAERR)

    except neuromation.client.ResourceNotFound as error:
        log.error(f"{error}")
        sys.exit(os.EX_OSFILE)

    except neuromation.client.AuthenticationError as error:
        log.error(f"Cannot authenticate ({error})")
        sys.exit(os.EX_NOPERM)
    except neuromation.client.AuthorizationError as error:
        log.error(f"You haven`t enough permission ({error})")
        sys.exit(os.EX_NOPERM)

    except neuromation.client.ClientError as error:
        log.error(f"Application error ({error})")
        sys.exit(os.EX_SOFTWARE)

    except aiohttp.ClientError as error:
        log.error(f"Connection error ({error})")
        sys.exit(os.EX_IOERR)

    except FileNotFoundError as error:
        log.error(f"File not found ({error})")
        sys.exit(os.EX_OSFILE)
    except NotADirectoryError as error:
        log.error(f"{error}")
        sys.exit(os.EX_OSFILE)
    except PermissionError as error:
        log.error(f"Cannot access file ({error})")
        sys.exit(os.EX_NOPERM)
    except IOError as error:
        log.error(f"I/O Error ({error})")
        raise error

    except KeyboardInterrupt:
        log.error("Aborting.")
        sys.exit(130)
    except ValueError as e:
        print(e)
        sys.exit(127)

    except Exception as e:
        log.error(f"{e}")
        raise e
