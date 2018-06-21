import sys
from functools import partial
from urllib.parse import urlparse

import neuromation
from neuromation.client import Storage

from .commands import command, run

# For stream copying from file to http or from http to file
BUFFER_SIZE_MB = 16


@command
def nm(url, token, version):
    """
    Deep network training, inference and datasets with Neuromation Platform

    Usage:
      nm URL [options] COMMAND

    Options:
      -t, --token TOKEN           API authentication token (not implemented)
      -v, --version               Print version and exit

    Commands:
      job                Start, stop, pause and monitor training and inference
      help               Get help on a command
      storage            Storage operations
    """

    @command
    def storage():
        """
        Usage:
            nm storage COMMAND

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
                nm storage rm PATH

            Remove files or directories
            """
            with storage() as s:
                return s.rm(path=path)

        @command
        def ls(path):
            """
            Usage:
                nm storage ls PATH

            List directory contents
            """
            with storage() as s:
                return '\n'.join(s.ls(path=path))

        @command
        def cp(source, destination):
            """
            Usage:
                nm storage cp SOURCE DESTINATION

            Copy files and directories
            """

            def transfer(i, o):
                while True:
                    buf = o.read(size=BUFFER_SIZE_MB * 1024 * 1024)

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
                nm storage mkdir [PATH ...]

            Make directories
            """
            with storage() as s:
                return '\n'.join(s.ls(path=path))
        return locals()
    return locals()


def main():
    try:
        res = run(
            root=nm,
            argv=sys.argv[1:],
            version=f'Neuromation Platform Client {neuromation.__version__}')
    except Exception as e:
        print(e)
        return

    if res:
        print(res)
