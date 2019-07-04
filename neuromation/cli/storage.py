import logging
from typing import Optional, Sequence

import click
from yarl import URL

from .command_progress_report import ProgressBase
from .formatters import (
    BaseFilesFormatter,
    FilesSorter,
    LongFilesFormatter,
    SimpleFilesFormatter,
    VerticalColumnsFilesFormatter,
)
from .root import Root
from .utils import async_cmd, command, group, parse_file_resource


log = logging.getLogger(__name__)


@group()
def storage() -> None:
    """
    Storage operations.
    """


@command()
@click.argument("paths", nargs=-1, required=True)
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    help="remove directories and their contents recursively",
)
@async_cmd()
async def rm(root: Root, paths: Sequence[str], recursive: bool) -> None:
    """
    Remove files or directories.

    Examples:

    neuro rm storage:///foo/bar
    neuro rm storage:/foo/bar
    neuro rm storage://{username}/foo/bar
    neuro rm --recursive storage://{username}/foo/
    """
    for path in paths:
        uri = parse_file_resource(path, root)

        await root.client.storage.rm(uri, recursive=recursive)
        if root.verbosity > 0:
            click.echo(f"removed {str(uri)!r}")


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
    root: Root, paths: Sequence[str], human_readable: bool, format_long: bool, sort: str
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

        uri = parse_file_resource(path, root)
        if root.verbosity > 0:
            click.echo(f"List of {str(uri)!r}:")

        files = await root.client.storage.ls(uri)

        files = sorted(files, key=FilesSorter(sort).key())

        for line in formatter.__call__(files):
            click.echo(line)


@command()
@click.argument("sources", nargs=-1, required=False)
@click.argument("destination", required=False)
@click.option("-r", "--recursive", is_flag=True, help="Recursive copy, off by default")
@click.option(
    "-t",
    "--target-directory",
    metavar="DIRECTORY",
    default=None,
    help="Copy all SOURCES into DIRECTORY",
)
@click.option(
    "-T",
    "--no-target-directory",
    is_flag=True,
    help="Treat DESTINATION as a normal file",
)
@click.option("-p", "--progress", is_flag=True, help="Show progress, off by default")
@async_cmd()
async def cp(
    root: Root,
    sources: Sequence[str],
    destination: str,
    recursive: bool,
    target_directory: str,
    no_target_directory: bool,
    progress: bool,
) -> None:
    """
    Copy files and directories.

    Either SOURCES or DESTINATION should have storage:// scheme.
    If scheme is omitted, file:// scheme is assumed.

    Use /dev/stdin and /dev/stdout file names to copy a file from terminal
    and print the content of file on the storage to console.

    Examples:

    # copy local file ./foo into remote storage root
    neuro cp ./foo storage:///
    neuro cp ./foo storage:/

    # download remote file foo into local file foo with
    # explicit file:// scheme set
    neuro cp storage:///foo file:///foo
    """
    target_dir: Optional[URL]
    dst: Optional[URL]
    if target_directory:
        if no_target_directory:
            raise click.UsageError(
                "Cannot combine --target-directory (-t) and --no-target-directory (-T)"
            )
        if destination is None:
            raise click.MissingParameter(
                param_type="argument", param_hint='"SOURCES..."'
            )
        sources = *sources, destination
        target_dir = parse_file_resource(target_directory, root)
        dst = None
    else:
        if destination is None:
            raise click.MissingParameter(
                param_type="argument", param_hint='"DESTINATION"'
            )
        if not sources:
            raise click.MissingParameter(
                param_type="argument", param_hint='"SOURCES..."'
            )
        dst = parse_file_resource(destination, root)
        if no_target_directory:
            if len(sources) > 1:
                raise click.UsageError(f"Extra operand after {sources[1]!r}")
            target_dir = None
        elif await root.client.storage._is_dir(dst):
            target_dir = dst
            dst = None
        else:
            target_dir = None

    for source in sources:
        src = parse_file_resource(source, root)

        progress_obj = ProgressBase.create_progress(progress, root.verbosity > 0)

        if target_dir:
            dst = target_dir / src.name
        assert dst
        if src.scheme == "file" and dst.scheme == "storage":
            if recursive:
                await root.client.storage.upload_dir(src, dst, progress=progress_obj)
            else:
                await root.client.storage.upload_file(src, dst, progress=progress_obj)
        elif src.scheme == "storage" and dst.scheme == "file":
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
@click.option(
    "-p",
    "--parents",
    is_flag=True,
    help="No error if existing, make parent directories as needed",
)
@async_cmd()
async def mkdir(root: Root, paths: Sequence[str], parents: bool) -> None:
    """
    Make directories.
    """

    for path in paths:
        uri = parse_file_resource(path, root)

        await root.client.storage.mkdirs(uri, parents=parents, exist_ok=parents)
        if root.verbosity > 0:
            click.echo(f"created directory {str(uri)!r}")


@command()
@click.argument("sources", nargs=-1, required=True)
@click.argument("destination")
@async_cmd()
async def mv(root: Root, sources: Sequence[str], destination: str) -> None:
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

    dst = parse_file_resource(destination, root)
    for source in sources:
        src = parse_file_resource(source, root)

        await root.client.storage.mv(src, dst)
        if root.verbosity > 0:
            click.echo(f"{str(src)!r} -> {str(dst)!r}")


storage.add_command(cp)
storage.add_command(ls)
storage.add_command(rm)
storage.add_command(mkdir)
storage.add_command(mv)
