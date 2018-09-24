import logging
import subprocess
import sys
from functools import partial
from pathlib import Path
from urllib.parse import urlparse

from aiohttp import ClientConnectorError

import neuromation
from neuromation.cli.command_handlers import (CopyOperation,
                                              PlatformListDirOperation,
                                              PlatformMakeDirOperation)
from neuromation.logging import ConsoleWarningFormatter

from . import rc
from .commands import command, dispatch

# For stream copying from file to http or from http to file
BUFFER_SIZE_MB = 16
MONITOR_BUFFER_SIZE_BYTES = 256

RC_PATH = Path.home().joinpath('.nmrc')

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
        @command
        def url(url):
            """
            Usage:
                neuro config url URL

            Updates API URL
            """
            config = rc.load(RC_PATH)
            config = rc.Config(url=url, auth=config.auth)
            rc.save(RC_PATH, config)

        @command
        def show():
            """
            Usage:
                neuro config show

            Prints current settings
            """
            config = rc.load(RC_PATH)
            print(config)

        @command
        def auth(token):
            """
            Usage:
                neuro config auth TOKEN

            Updates authorization token
            """
            # TODO update docker authorization here
            # TODO (R Zubairov, 09/13/2018): check token correct
            # connectivity, check with Alex
            # Do not overwrite token in case new one does not work
            # TODO (R Zubairov, 09/13/2018): on server side we shall implement
            # protection against brute-force

            config = rc.load(RC_PATH)
            config = rc.Config(url=config.url, auth=token)
            rc.save(RC_PATH, config)

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

            Remove files or directories
            """
            with storage() as s:
                return s.rm(path=path)

        @command
        def ls(path):
            """
            Usage:
                neuro store ls PATH

            List directory contents
            """
            format = '{type:<15}{size:<15,}{name:<}'.format

            storage_objects = PlatformListDirOperation().ls(path, storage)

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

            operation = CopyOperation.create(src.scheme, dst.scheme, recursive)

            if operation:
                return operation.copy(src, dst, storage)

            raise ValueError('Invalid SOURCE or DESTINATION value')

        @command
        def mkdir(path):
            """
            Usage:
                neuro store mkdir PATH

            Make directories
            """
            PlatformMakeDirOperation().mkdir(path, storage)
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

        from neuromation.client.jobs import Model, Image, Resources

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

            cmd = ' '.join(cmd)
            log.debug(f'cmd="{cmd}"')

            cpu = float(cpu)
            gpu = int(gpu)
            extshm = bool(extshm)

            with model() as m:
                job = m.train(
                    image=Image(
                            image=image,
                            command=cmd),
                    resources=Resources(
                        memory=memory,
                        gpu=gpu,
                        cpu=cpu,
                        shm=extshm
                    ),
                    dataset=dataset,
                    results=results)

            # Format job info properly
            return f'Job ID: {job.id} Status: {job.status}\n' + \
                   f'Shortcuts:\n' + \
                   f'  neuro job status {job.id}  # check job status\n' + \
                   f'  neuro job monitor {job.id} # monitor job stdout\n' + \
                   f'  neuro job kill {job.id}    # kill job'

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
          list List your docker images
        """
        @command
        def push(image_name):
            """
            Usage:
                neuro image push IMAGE_NAME

            Push docker image into cloud registry
            """
            config = rc.load(RC_PATH)
            docker_registry_url = config.docker_registry_url()
            process = subprocess.run(
                args=['docker1', 'push',
                      f'http://{docker_registry_url}/{image_name}'],
                capture_output=True)

            if process.returncode != 0:
                raise ValueError(f'Docker pull failed. '
                                 f'Error code {process.returncode}')

            return locals()

        @command
        def pull(image):
            """
            Usage:
                neuro image pull IMAGE

            Pull docker image into cloud registry
            """

            return locals()

        @command
        def list():
            """
            Usage:
                neuro image list

            Lists docker images available
            """
            # TODO implement
            print('Not implemented YET')
            return locals()
    return locals()


def main():
    setup_logging()
    setup_console_handler(console_handler, verbose=('--verbose' in sys.argv))

    version = f'Neuromation Platform Client {neuromation.__version__}'
    if '-v' in sys.argv:
        print(version)
        sys.exit(0)

    config = rc.load(RC_PATH)
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
    except ClientConnectorError:
        log.error('Error connecting to server.')
        sys.exit(126)
    except KeyboardInterrupt:
        log.error("Aborting.")
        sys.exit(130)
    except ValueError as e:
        print(e)
        sys.exit(127)
    except Exception as e:
        log.error(f'{e}')
        raise e
