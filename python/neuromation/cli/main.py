import logging
import os
import subprocess
import sys
from functools import partial
from urllib.parse import urlparse

import aiohttp

import neuromation
from neuromation.cli.command_handlers import (CopyOperation,
                                              ModelHandlerOperations,
                                              PlatformListDirOperation,
                                              PlatformMakeDirOperation,
                                              PlatformRemoveOperation)
from neuromation.cli.rc import Config
from neuromation.logging import ConsoleWarningFormatter

from . import rc
from .commands import command, dispatch

# For stream copying from file to http or from http to file
BUFFER_SIZE_MB = 16
MONITOR_BUFFER_SIZE_BYTES = 256

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
    if not handler.stream.closed and \
           handler.stream.isatty() and \
           noansi is False:
        format_class = ConsoleWarningFormatter
    else:
        format_class = logging.Formatter

    if verbose:
        handler.setFormatter(
            format_class('%(name)s.%(funcName)s: %(message)s'))
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
  -u, --url URL         Override API URL [default: {url}]
  -t, --token TOKEN     API authentication token (not implemented)
  --verbose             Enable verbose logging
  -v, --version         Print version and exit

Commands:
  model                 Model training, testing and inference
  job                   Manage existing jobs
  store                 Storage operations
  config                Configure API connection settings
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
            show            Print current settings
        """
        def update_docker_config(config: rc.Config) -> None:
            docker_registry_url = config.docker_registry_url()

            process = subprocess.run(['docker', 'login',
                                      '-p', token,
                                      '-u', 'token',
                                      docker_registry_url])
            if process.returncode != 0:
                raise ValueError('Failed to updated docker auth details.')

        @command
        def url(url):
            """
            Usage:
                neuro config url URL

            Updates API URL
            """
            config = rc.ConfigFactory.load()
            config = rc.Config(url=url, auth=config.auth)
            rc.ConfigFactory.save(config)
            update_docker_config(config)

        @command
        def show():
            """
            Usage:
                neuro config show

            Prints current settings
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

            config = rc.ConfigFactory.load()
            config = rc.Config(url=config.url, auth=token)
            rc.ConfigFactory.save(config)
            update_docker_config(config)

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
                neuro store rm storage://alice/foo/bar/
            """
            config = rc.ConfigFactory.load()
            platform_user_name = config.get_platform_user_name()
            PlatformRemoveOperation(platform_user_name).remove(path, storage)

        @command
        def ls(path):
            """
            Usage:
                neuro store ls PATH

            List directory contents
            """
            format = '{type:<15}{size:<15,}{name:<}'.format

            config = rc.ConfigFactory.load()
            platform_user_name = config.get_platform_user_name()
            ls_op = PlatformListDirOperation(platform_user_name)
            storage_objects = ls_op.ls(path, storage)

            print('\n'.join(
                format(type=status.type.lower(),
                       name=status.path,
                       size=status.size)
                for status in storage_objects))

        @command
        def cp(source, destination, recursive):
            """
            Usage:
                neuro store cp [options] SOURCE DESTINATION

            Copy files and directories
            Either SOURCE or DESTINATION should have storage:// scheme.
            If scheme is omitted, file:// scheme is assumed.

            Options:
              -r, --recursive             Recursive copy

            Example:

            # copy local file ./foo into remote storage root
            neuro store cp ./foo storage:///

            # download remote file foo into local file foo with
            # explicit file:// scheme set
            neuro store cp storage:///foo file:///foo
            """
            src = urlparse(source, scheme='file')
            dst = urlparse(destination, scheme='file')

            log.debug(f'src={src}')
            log.debug(f'dst={dst}')

            config = rc.ConfigFactory.load()
            platform_user_name = config.get_platform_user_name()
            operation = CopyOperation.create(platform_user_name,
                                             src.scheme,
                                             dst.scheme,
                                             recursive)

            if operation:
                return operation.copy(src, dst, storage)

            raise neuromation.client.IllegalArgumentError('Invalid SOURCE or '
                                                          'DESTINATION value')

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
        """

        from neuromation.client.jobs import Model

        model = partial(Model, url, token)

        @command
        def train(image, dataset, results, gpu, cpu, memory, extshm, cmd):
            """
            Usage:
                neuro model train [options] IMAGE DATASET RESULTS CMD [CMD ...]

            Start training job using model from IMAGE, dataset from DATASET and
            store output weights in RESULTS.

            COMMANDS list will be passed as commands to model container.

            Options:
                -g, --gpu NUMBER      Number of GPUs to request [default: 1]
                -c, --cpu NUMBER      Number of CPUs to request [default: 1.0]
                -m, --memory AMOUNT   Memory amount to request [default: 16G]
                -x, --extshm          Request extended '/dev/shm' space.
            """

            config: Config = rc.ConfigFactory.load()
            platform_user_name = config.get_platform_user_name()
            model_operation = ModelHandlerOperations(platform_user_name)
            return model_operation.train(image, dataset, results,
                                         gpu, cpu, memory, extshm,
                                         cmd, model)

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
          monitor             Monitor job output stream
          list                List all jobs
          status              Display status of a job
          kill                Kill job
        """

        from neuromation.client.jobs import Job, JobStatus
        jobs = partial(Job, url, token)

        @command
        def monitor(id):
            """
            Usage:
                neuro job monitor ID

            Monitor job output stream
            """
            with jobs() as j:
                with j.monitor(id) as stream:
                    while True:
                        chunk = stream.read(MONITOR_BUFFER_SIZE_BYTES)
                        if not chunk:
                            break
                        sys.stdout.write(chunk.decode(errors='ignore'))

        @command
        def list():
            """
            Usage:
                neuro job list

            List all jobs
            """
            with jobs() as j:
                return '\n'.join([
                        f'{item.id}    {item.status}'
                        for item in
                        j.list()
                    ])

        @command
        def status(id):
            """
            Usage:
                neuro job status ID

            Display status of a job
            """
            with jobs() as j:
                res = j.status(id)
                result = f'Job: {res.id}\n' \
                         f'Status: {res.status}\n' \
                         f'Created: {res.history.created_at}'
                if res.status in [JobStatus.RUNNING, JobStatus.FAILED,
                                  JobStatus.SUCCEEDED]:
                    result += '\n' \
                              f'Started: {res.history.started_at}'
                if res.status in [JobStatus.FAILED, JobStatus.SUCCEEDED]:
                    result += '\n' \
                              f'Finished: {res.history.finished_at}'
                if res.status == JobStatus.FAILED:
                    result += '\n' \
                              f'Reason: {res.history.reason}\n' \
                              '===Description===\n ' \
                              f'{res.history.description}\n================='
                return result

        @command
        def kill(id):
            """
            Usage:
                neuro job kill ID

            Kill job
            """
            with jobs() as j:
                j.kill(id)
            return 'Job killed.'
        return locals()

    @command
    def image():
        """
        Usage:
            neuro image COMMAND

        Docker image operations

        Commands:
          push Push docker image from local machine to cloud registry
          pull Pull docker image from cloud registry to local machine
          search List your docker images
        """
        def get_image_platform_full_name(image_name):
            config = rc.ConfigFactory.load()
            docker_registry_url = config.docker_registry_url()
            platform_user_name = config.get_platform_user_name()
            target_image_name = f'{docker_registry_url}/' \
                                f'{platform_user_name}/{image_name}'
            return target_image_name

        @command
        def push(image_name):
            """
            Usage:
                neuro image push IMAGE_NAME

            Push an image or a repository to a registry
            """
            target_image_name = get_image_platform_full_name(image_name)
            # Tag first, as otherwise it would fail
            try:
                subprocess.run(['docker', 'tag',
                                image_name, target_image_name],
                               check=True)
            except subprocess.CalledProcessError as e:
                raise ValueError(f'Docker tag failed. '
                                 f'Error code {e.returncode}')

            # PUSH Image to remote registry
            try:
                subprocess.run(['docker', 'push', target_image_name],
                               check=True)
            except subprocess.CalledProcessError as e:
                raise ValueError(f'Docker pull failed. '
                                 f'Error details {e.returncode}')

        @command
        def pull(image_name):
            """
            Usage:
                neuro image pull IMAGE_NAME

            Pull an image or a repository from a registry
            """
            target_image_name = get_image_platform_full_name(image_name)
            try:
                subprocess.run(['docker', 'pull', target_image_name],
                               check=True)
            except subprocess.CalledProcessError as e:
                raise ValueError(f'Docker pull failed. '
                                 f'Error code {e.returncode}')

        return locals()
    return locals()


def main():
    setup_logging()
    setup_console_handler(console_handler, verbose=('--verbose' in sys.argv))

    version = f'Neuromation Platform Client {neuromation.__version__}'
    if '-v' in sys.argv:
        print(version)
        sys.exit(0)

    config = rc.ConfigFactory.load()
    neuro.__doc__ = neuro.__doc__.format(
            url=config.url
        )

    try:
        res = dispatch(
            target=neuro,
            tail=sys.argv[1:],
            token=config.auth)
        if res:
            print(res)

    except neuromation.client.IllegalArgumentError as error:
        log.error(f'Illegal argument(s) ({error})')
        sys.exit(os.EX_DATAERR)

    except neuromation.client.ResourceNotFound as error:
        log.error(f'{error}')
        sys.exit(os.EX_OSFILE)

    except neuromation.client.AuthenticationError as error:
        log.error(f'Cannot authenticate ({error})')
        sys.exit(os.EX_NOPERM)
    except neuromation.client.AuthorizationError as error:
        log.error(f'You haven`t enough permission ({error})')
        sys.exit(os.EX_NOPERM)

    except neuromation.client.ClientError as error:
        log.error(f'Application error ({error})')
        sys.exit(os.EX_SOFTWARE)

    except aiohttp.ClientError as error:
        log.error(f'Connection error ({error})')
        sys.exit(os.EX_IOERR)

    except FileNotFoundError as error:
        log.error(f'File not found ({error})')
        sys.exit(os.EX_OSFILE)
    except PermissionError as error:
        log.error(f'Cannot access file ({error})')
        sys.exit(os.EX_NOPERM)
    except IOError as error:
        log.error(f'I/O Error ({error})')
        raise error

    except KeyboardInterrupt:
        log.error("Aborting.")
        sys.exit(130)
    except ValueError as e:
        print(e)
        sys.exit(127)

    except Exception as e:
        log.error(f'{e}')
        raise e
