import logging
import sys
from functools import partial
from pathlib import Path
from urllib.parse import urlparse

import neuromation
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
  help                  Get help on a command
    """

    from neuromation.client import Storage

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

        storage = partial(Storage, url)

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

            with storage() as s:
                print('\n'.join(
                    format(type=status.type.lower(), name=status.path, size=status.size)
                    for status in s.ls(path=path)))

        @command
        def cp(source, destination):
            """
            Usage:
                neuro store cp SOURCE DESTINATION

            Copy files and directories
            Either SOURCE or DESTINATION should have storage:// scheme.
            If scheme is omitted, file:// scheme is assumed.

            Example:

            # copy local file ./foo into remote storage root
            neuro store cp ./foo storage:///

            # download remote file foo into local file foo with
            # explicit file:// scheme set
            neuro store cp storage:///foo file:///foo
            """

            def transfer(i, o):
                log.debug(f'Input: {i}')
                log.debug(f'Output: {o}')

                while True:
                    buf = i.read(BUFFER_SIZE_MB * 1024 * 1024)

                    if not buf:
                        break

                    o.write(buf)

            src = urlparse(source, scheme='file')
            dst = urlparse(destination, scheme='file')

            log.debug(f'src={src}')
            log.debug(f'dst={dst}')

            if src.scheme == 'storage':
                if dst.scheme != 'file':
                    raise ValueError(
                        'storage:// and file:// schemes required')
                with storage() as s:
                    with s.open(path=src.path) as stream:
                        with open(dst.path, mode='wb') as f:
                            transfer(stream, f)
                            return destination

            if dst.scheme == 'storage':
                if src.scheme != 'file':
                    raise ValueError(
                        'storage:// and file:// schemes required')
                with open(src.path, mode='rb') as f:
                    with storage() as s:
                        s.create(path=dst.path, data=f)
                        return destination

            raise ValueError('Invalid SOURCE or DESTINATION value')

        @command
        def mkdir(path):
            """
            Usage:
                neuro store mkdir PATH

            Make directories
            """
            with storage() as s:
                return s.mkdirs(path=path)
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

        model = partial(Model, url)

        @command
        def train(image, dataset, results, gpu, cpu, memory, cmd):
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
            """

            cmd = ' '.join(cmd)
            log.debug(f'cmd="{cmd}"')

            cpu = float(cpu)
            gpu = int(gpu)

            with model() as m:
                job = m.train(
                    image=Image(
                            image=image,
                            command=cmd),
                    resources=Resources(
                        memory=memory,
                        gpu=gpu,
                        cpu=cpu),
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

        from neuromation.client.jobs import Job
        jobs = partial(Job, url)

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
                return f'{res.id}      {res.status}'

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
            tail=sys.argv[1:])
        if res:
            print(res)
    except KeyboardInterrupt:
        log.error("Aborting.")
        sys.exit(1)
    except ValueError as e:
        print(e)
        sys.exit(1)
    except Exception as e:
        log.error(f'{e}')
        raise e
