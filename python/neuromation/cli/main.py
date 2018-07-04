import logging
import sys
from functools import partial
from urllib.parse import urlparse

import neuromation

from .commands import command, dispatch
from .formatter import ConsoleWarningFormatter

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
    if handler.stream.isatty() and noansi is False:
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
def nmc(url, token, verbose, version):
    """
    Deep network training, inference and datasets with Neuromation Platform

    Usage:
      nmc URL [options] COMMAND

    Options:
      -t, --token TOKEN           API authentication token (not implemented)
      --verbose                   Enable verbose logging
      -v, --version               Print version and exit

    Commands:
      job                Start, stop, pause and monitor training and inference
      help               Get help on a command
      storage            Storage operations
    """

    from neuromation.client import Storage

    @command
    def storage():
        """
        Usage:
            nmc storage COMMAND

        Storage operations

        Commands:
          rm                 Remove files or directories
          ls                 List directory contents
          cp                 Copy files and directories
          mkdir              Make directories
          help               Get help on a command
        """

        storage = partial(Storage, url)

        @command
        def rm(path):
            """
            Usage:
                nmc storage rm PATH

            Remove files or directories
            """
            with storage() as s:
                return s.rm(path=path)

        @command
        def ls(path):
            """
            Usage:
                nmc storage ls PATH

            List directory contents
            """
            with storage() as s:
                return '\n'.join(s.ls(path=path))

        @command
        def cp(source, destination):
            """
            Usage:
                nmc storage cp SOURCE DESTINATION

            Copy files and directories
            """

            def transfer(i, o):
                log.debug(f'Input: {i}')
                log.debug(f'Output: {o}')

                while True:
                    buf = i.read(BUFFER_SIZE_MB * 1024 * 1024)

                    if not buf:
                        break

                    o.write(buf)

            src = urlparse(source)
            dst = urlparse(destination)

            if src.scheme == 'http':
                if dst.scheme:
                    raise ValueError(
                        'SOURCE or DESTINATION must have http scheme')
                with storage() as s:
                    stream = s.open(path=src.path)
                    with open(dst.path, mode='wb') as f:
                        return transfer(stream, f)

            if dst.scheme == 'http':
                if src.scheme:
                    raise ValueError(
                        'SOURCE or DESTINATION must have http scheme')
                with open(src.path, mode='rb') as f:
                    with storage() as s:
                        return s.create(path=dst.path, data=f)

            raise ValueError('Invalid SOURCE or DESTINATION value')

        @command
        def mkdir(path):
            """
            Usage:
                nmc storage mkdir [PATH ...]

            Make directories
            """
            with storage() as s:
                return '\n'.join(s.ls(path=path))
        return locals()

    return locals()


def main():
    setup_logging()
    setup_console_handler(console_handler, verbose=('--verbose' in sys.argv))
    res = ''

    try:
        res = dispatch(
            target=nmc,
            tail=sys.argv[1:],
            version=f'Neuromation Platform Client {neuromation.__version__}')
    except KeyboardInterrupt:
        log.error("Aborting.")
        sys.exit(1)
    except Exception as e:
        log.error(f'nmc: {e}')
    finally:
        if res:
            print(f'Success: {res}')
