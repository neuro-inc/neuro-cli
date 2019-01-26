import logging

import aiohttp
import click
from yarl import URL

from .command_progress_report import ProgressBase
from .formatter import StorageLsFormatter
from .utils import Context, run_async


log = logging.getLogger(__name__)


@click.group()
def storage() -> None:
    """
    Storage operations.
    """


@storage.command()
@click.argument("path")
@click.pass_obj
@run_async
async def rm(ctx: Context, path: str) -> None:
    """
    Remove files or directories.

    Examples:

    \b
    neuro storage rm storage:///foo/bar/
    neuro storage rm storage:/foo/bar/
    neuro storage rm storage://{username}/foo/bar/
    """
    uri = URL(path)

    async with ctx.make_client() as client:
        await client.storage.rm(uri)


@storage.command()
@click.argument("path", default="storage://~")
@click.pass_obj
@run_async
async def ls(ctx: Context, path: str) -> None:
    """
    List directory contents.

    By default PATH is equal user`s home dir (storage:)
    """
    uri = URL(path)

    async with ctx.make_client() as client:
        res = await client.storage.ls(uri)

    click.echo(StorageLsFormatter().fmt_long(res))


@storage.command()
@click.argument("source")
@click.argument("destination")
@click.option("-r", "--recursive", is_flag=True, help="Recursive copy, off by default")
@click.option("-p", "--progress", is_flag=True, help="Show progress, off by default")
@click.pass_obj
@run_async
async def cp(
    ctx: Context, source: str, destination: str, recursive: bool, progress: bool
) -> None:
    """
    Copy files and directories.

    Either SOURCE or DESTINATION should have storage:// scheme.
    If scheme is omitted, file:// scheme is assumed.

    Examples:

    \b
    # copy local file ./foo into remote storage root
    neuro storage cp ./foo storage:///
    neuro storage cp ./foo storage:/

    \b
    # download remote file foo into local file foo with
    # explicit file:// scheme set
    neuro storage cp storage:///foo file:///foo
    """
    timeout = aiohttp.ClientTimeout(
        total=None, connect=None, sock_read=None, sock_connect=30
    )
    src = URL(source)
    dst = URL(destination)

    log.debug(f"src={src}")
    log.debug(f"dst={dst}")

    progress_obj = ProgressBase.create_progress(progress)
    if not src.scheme:
        src = URL("file:" + src.path)
    if not dst.scheme:
        dst = URL("file:" + dst.path)
    async with ctx.make_client(timeout=timeout) as client:
        if src.scheme == "file" and dst.scheme == "storage":
            if recursive:
                await client.storage.upload_dir(progress_obj, src, dst)
            else:
                await client.storage.upload_file(progress_obj, src, dst)
        elif src.scheme == "storage" and dst.scheme == "file":
            if recursive:
                await client.storage.download_dir(progress_obj, src, dst)
            else:
                await client.storage.download_file(progress_obj, src, dst)
        else:
            raise RuntimeError(f"Copy operation for {src} -> {dst} is not supported")


@storage.command()
@click.argument("path")
@click.pass_obj
@run_async
async def mkdir(ctx: Context, path: str) -> None:
    """
    Make directories.
    """

    uri = URL(path)

    async with ctx.make_client() as client:
        await client.storage.mkdirs(uri)


@storage.command()
@click.argument("source")
@click.argument("destination")
@click.pass_obj
@run_async
async def mv(ctx: Context, source: str, destination: str) -> None:
    """
    Move or rename files and directories.

    SOURCE must contain path to the
    file or directory existing on the storage, and DESTINATION must contain
    the full path to the target file or directory.


    Examples:

    \b
    # move or rename remote file
    neuro storage mv storage://{username}/foo.txt storage://{username}/bar.txt
    neuro storage mv storage://{username}/foo.txt storage://~/bar/baz/foo.txt

    \b
    # move or rename remote directory
    neuro storage mv storage://{username}/foo/ storage://{username}/bar/
    neuro storage mv storage://{username}/foo/ storage://{username}/bar/baz/foo/
    """

    src = URL(source)
    dst = URL(destination)

    async with ctx.make_client() as client:
        await client.storage.mv(src, dst)
