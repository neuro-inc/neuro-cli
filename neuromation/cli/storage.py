import logging
from typing import List

import click

from neuromation.api.url_utils import uri_from_cli

from .command_progress_report import ProgressBase
from .formatters import (
    BaseFilesFormatter,
    FilesSorter,
    LongFilesFormatter,
    SimpleFilesFormatter,
    VerticalColumnsFilesFormatter,
)
from .root import Root
from .utils import async_cmd, command, group


log = logging.getLogger(__name__)


@group()
def storage() -> None:
    """
    Storage operations.
    """


@command()
@click.argument("paths", nargs=-1, required=True)
@async_cmd()
async def rm(root: Root, paths: List[str]) -> None:
    """
    Remove files or directories.

    Examples:

    neuro rm storage:///foo/bar/
    neuro rm storage:/foo/bar/
    neuro rm storage://{username}/foo/bar/
    """
    for path in paths:
        uri = uri_from_cli(path, root.username)
        log.info(f"Using path '{uri}'")

        await root.client.storage.rm(uri)


@command()
@click.argument("paths", nargs=-1)
@click.option(
    "--human-readable",
    "-h",
    is_flag=True,
    help="with -l print human readable sizes (e.g., 2K, 540M)",
)
@click.option("-l", "format_long", is_flag=True, help="use a long listing format")
@click.option(
    "--sort",
    type=click.Choice(["name", "size", "time"]),
    default="name",
    help="sort by given field, default is name",
)
@async_cmd()
async def ls(
    root: Root, paths: List[str], human_readable: bool, format_long: bool, sort: str
) -> None:
    """
    List directory contents.

    By default PATH is equal user`s home dir (storage:)
    """
    if not paths:
        paths = ["storage://~"]
    for path in paths:
        if format_long:
            formatter: BaseFilesFormatter = LongFilesFormatter(
                human_readable=human_readable, color=root.color
            )
        else:
            if root.tty:
                formatter = VerticalColumnsFilesFormatter(
                    width=root.terminal_size[0], color=root.color
                )
            else:
                formatter = SimpleFilesFormatter(root.color)

        uri = uri_from_cli(path, root.username)
        log.info(f"Using path '{uri}'")

        files = await root.client.storage.ls(uri)

        files = sorted(files, key=FilesSorter(sort).key())

        for line in formatter.__call__(files):
            click.echo(line)


@command()
@click.argument("sources", nargs=-1, required=True)
@click.argument("destination")
@click.option("-r", "--recursive", is_flag=True, help="Recursive copy, off by default")
@click.option("-p", "--progress", is_flag=True, help="Show progress, off by default")
@async_cmd()
async def cp(
    root: Root, sources: List[str], destination: str, recursive: bool, progress: bool
) -> None:
    """
    Copy files and directories.

    Either SOURCES or DESTINATION should have storage:// scheme.
    If scheme is omitted, file:// scheme is assumed.

    Examples:

    # copy local file ./foo into remote storage root
    neuro cp ./foo storage:///
    neuro cp ./foo storage:/

    # download remote file foo into local file foo with
    # explicit file:// scheme set
    neuro cp storage:///foo file:///foo
    """
    dst = uri_from_cli(destination, root.username)
    log.info(f"Using destination path: '{dst}'")

    for source in sources:
        src = uri_from_cli(source, root.username)

        progress_obj = ProgressBase.create_progress(progress)

        if src.scheme == "file" and dst.scheme == "storage":
            log.info(f"Using source path:      '{src}'")
            if recursive:
                await root.client.storage.upload_dir(src, dst, progress=progress_obj)
            else:
                await root.client.storage.upload_file(src, dst, progress=progress_obj)
        elif src.scheme == "storage" and dst.scheme == "file":
            log.info(f"Using source path:      '{src}'")
            if recursive:
                await root.client.storage.download_dir(src, dst, progress=progress_obj)
            else:
                await root.client.storage.download_file(src, dst, progress=progress_obj)
        else:
            raise RuntimeError(
                f"Copy operation of the file with scheme '{src.scheme}'"
                f" to the file with scheme '{dst.scheme}'"
                f" is not supported"
            )


@command()
@click.argument("paths", nargs=-1, required=True)
@async_cmd()
async def mkdir(root: Root, paths: List[str]) -> None:
    """
    Make directories.
    """

    for path in paths:
        uri = uri_from_cli(path, root.username)
        log.info(f"Using path '{uri}'")

        await root.client.storage.mkdirs(uri)


@command()
@click.argument("sources", nargs=-1, required=True)
@click.argument("destination")
@async_cmd()
async def mv(root: Root, sources: List[str], destination: str) -> None:
    """
    Move or rename files and directories.

    SOURCE must contain path to the
    file or directory existing on the storage, and DESTINATION must contain
    the full path to the target file or directory.


    Examples:

    # move or rename remote file
    neuro mv storage://{username}/foo.txt storage://{username}/bar.txt
    neuro mv storage://{username}/foo.txt storage://~/bar/baz/foo.txt

    # move or rename remote directory
    neuro mv storage://{username}/foo/ storage://{username}/bar/
    neuro mv storage://{username}/foo/ storage://{username}/bar/baz/foo/
    """

    dst = uri_from_cli(destination, root.username)
    log.info(f"Using destination path: '{dst}'")
    for source in sources:
        src = uri_from_cli(source, root.username)
        log.info(f"Using source path:      '{src}'")

        await root.client.storage.mv(src, dst)


storage.add_command(cp)
storage.add_command(ls)
storage.add_command(rm)
storage.add_command(mkdir)
storage.add_command(mv)
