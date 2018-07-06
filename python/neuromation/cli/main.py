import logging
import sys
from functools import partial
from urllib.parse import urlparse

import neuromation
from neuromation.logging import ConsoleWarningFormatter

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
      store              Storage operations
      help               Get help on a command
    """

    from neuromation.client import Storage

    @command
    def store():
        """
        Usage:
            nmc store COMMAND

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
                nmc store rm PATH

            Remove files or directories
            """
            with storage() as s:
                return s.rm(path=path)

        @command
        def ls(path):
            """
            Usage:
                nmc store ls PATH

            List directory contents
            """
            with storage() as s:
                print('\n'.join(status.path for status in s.ls(path=path)))

        @command
        def cp(source, destination):
            """
            Usage:
                nmc store cp SOURCE DESTINATION

            Copy files and directories
            Either SOURCE or DESTINATION should have storage:// scheme.
            If scheme is omitted, file:// scheme is assumed.

            Example:

            # copy local file ./foo into remote storage root
            nmc store cp ./foo storage:///

            # download remote file foo into local file foo with
            # explicit file:// scheme set
            nmc store cp storage:///foo file:///foo
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
                    stream = s.open(path=src.path)
                    with open(dst.path, mode='wb') as f:
                        transfer(stream, f)
                        return dst.path

            if dst.scheme == 'storage':
                if src.scheme != 'file':
                    raise ValueError(
                        'storage:// and file:// schemes required')
                with open(src.path, mode='rb') as f:
                    with storage() as s:
                        return s.create(path=dst.path, data=f)

            raise ValueError('Invalid SOURCE or DESTINATION value')

        @command
        def mkdir(path):
            """
            Usage:
                nmc store mkdir PATH

            Make directories
            """
            with storage() as s:
                return '\n'.join(s.mkdirs(path=path))
        return locals()

    return locals()


def main():
    setup_logging()
    setup_console_handler(console_handler, verbose=('--verbose' in sys.argv))

    version = f'Neuromation Platform Client {neuromation.__version__}'
    if '-v' in sys.argv:
        print(version)
        sys.exit(0)

    try:
        dispatch(
            target=nmc,
            tail=sys.argv[1:])
    except KeyboardInterrupt:
        log.error("Aborting.")
        sys.exit(1)
    except ValueError as e:
        print(e)
        sys.exit(1)
    except Exception as e:
        log.error(f'{e}')
