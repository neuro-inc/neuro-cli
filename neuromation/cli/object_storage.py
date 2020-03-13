import glob as globmodule  # avoid conflict with subcommand "glob"
import logging
import sys
from typing import List, Optional, Sequence, Tuple

import click
from yarl import URL

from neuromation.api import IllegalArgumentError, ResourceNotFound
from neuromation.api.file_filter import FileFilter
from neuromation.api.object_storage import FileStatusType, ObjStatus
from neuromation.api.url_utils import _extract_path

from .const import EX_OSFILE
from .formatters import (
    BaseFilesFormatter,
    LongFilesFormatter,
    SimpleFilesFormatter,
    VerticalColumnsFilesFormatter,
    create_storage_progress,
    get_painter,
)
from .root import Root
from .storage import calc_filters, filter_option
from .utils import (
    command,
    group,
    option,
    pager_maybe,
    parse_obj_or_file_resource,
    parse_obj_resource,
)


log = logging.getLogger(__name__)


@group(name="obj")
def object_storage() -> None:
    """
    Object storage operations.
    """


@command()
@click.argument("paths", nargs=-1)
@option(
    "--human-readable",
    "-h",
    is_flag=True,
    help="with -l print human readable sizes (e.g., 2K, 540M).",
)
@option("-l", "format_long", is_flag=True, help="use a long listing format.")
@option(
    "--sort",
    type=click.Choice(["name", "size", "time"]),
    default="name",
    help="sort by given field, default is name.",
)
@option(
    "-r",
    "--recursive",
    is_flag=True,
    help="List all keys under the URL path provided, not just 1 level depths.",
)
async def ls(
    root: Root,
    paths: Sequence[str],
    human_readable: bool,
    format_long: bool,
    sort: str,
    recursive: bool,
) -> None:
    """
    List directory contents.

    By default PATH is equal user's home dir (storage:)
    """
    uris = [parse_obj_resource(path, root) for path in paths]

    obj = root.client.obj

    obj_listings: List[List[ObjStatus]] = []

    if not uris:
        # List Buckets instead of objects in bucket
        listing = await obj.list_buckets()
        obj_listings.append(listing)
    else:
        for uri in uris:
            bucket_name = uri.host
            assert bucket_name

            listing = await obj.list_objects(
                bucket_name=bucket_name,
                prefix=uri.path.lstrip("/"),
                recursive=recursive,
            )
            obj_listings.append(listing)

    formatter: BaseFilesFormatter
    if format_long:
        formatter = LongFilesFormatter(human_readable=human_readable, color=root.color)
    else:
        if root.tty:
            formatter = VerticalColumnsFilesFormatter(
                width=root.terminal_size[0], color=root.color
            )
        else:
            formatter = SimpleFilesFormatter(root.color)

    if len(obj_listings) > 1:
        buffer = []
        for uri, listing in zip(uris, obj_listings):
            buffer.append(click.style(str(uri), bold=True) + ":")
            buffer.extend(formatter(listing))
        pager_maybe("".join(buffer), root.tty, root.terminal_size)
    else:
        assert obj_listings
        pager_maybe(formatter(obj_listings[0]), root.tty, root.terminal_size)


@command()
@click.argument("patterns", nargs=-1, required=False)
async def glob(root: Root, patterns: Sequence[str]) -> None:
    """
    List resources that match PATTERNS.
    """
    for pattern in patterns:
        uri = parse_obj_resource(pattern, root)
        if root.verbosity > 0:
            painter = get_painter(root.color, quote=True)
            curi = painter.paint(str(uri), FileStatusType.FILE)
            click.echo(f"Using pattern {curi}:")
        assert uri.host
        if globmodule.has_magic(uri.host):
            raise ValueError(
                "You can not glob on bucket names. Please provide name explicitly."
            )
        objects = await root.client.obj.glob_objects(
            bucket_name=uri.host, pattern=uri.path
        )
        for obj in objects:
            click.echo(obj.uri)


@command()
@click.argument("sources", nargs=-1, required=False)
@click.argument("destination", required=False)
@option("-r", "--recursive", is_flag=True, help="Recursive copy, off by default")
@option(
    "--glob/--no-glob",
    is_flag=True,
    default=True,
    show_default=True,
    help="Expand glob patterns in SOURCES with explicit scheme.",
)
@option(
    "-t",
    "--target-directory",
    metavar="DIRECTORY",
    default=None,
    help="Copy all SOURCES into DIRECTORY.",
)
@option(
    "-T",
    "--no-target-directory",
    is_flag=True,
    help="Treat DESTINATION as a normal file.",
)
@filter_option(
    "--exclude",
    "filters",
    flag_value=True,
    help=(
        "Exclude files and directories that match the specified pattern. "
        "The default can be changed using the storage.cp-exclude "
        'configuration variable documented in "neuro help user-config"'
    ),
)
@filter_option(
    "--include",
    "filters",
    flag_value=False,
    help=(
        "Don't exclude files and directories that match the specified pattern. "
        "The default can be changed using the storage.cp-exclude "
        'configuration variable documented in "neuro help user-config"'
    ),
)
@option(
    "-p/-P",
    "--progress/--no-progress",
    is_flag=True,
    default=True,
    help="Show progress, on by default.",
)
async def cp(
    root: Root,
    sources: Sequence[str],
    destination: Optional[str],
    recursive: bool,
    glob: bool,
    target_directory: Optional[str],
    no_target_directory: bool,
    filters: Optional[Tuple[Tuple[bool, str], ...]],
    progress: bool,
) -> None:
    """
    Simple utility to copy files and directories into and from Object Storage.

    Either SOURCES or DESTINATION should have `object://` scheme.
    If scheme is omitted, file:// scheme is assumed. It is currently not possible to
    copy files between Object Storage (`object://`) destination, nor with `storage://`
    scheme paths.

    Use `/dev/stdin` and `/dev/stdout` file names to upload a file from standard input
    or output to stdout.

    File permissions, modification times and other attributes will not be passed to
    Object Storage metadata during upload.

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
        target_dir = parse_obj_or_file_resource(target_directory, root)
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
        dst = parse_obj_or_file_resource(destination, root)

        # From gsutil:
        #
        # There's an additional wrinkle when working with subdirectories: the resulting
        # names depend on whether the destination subdirectory exists. For example,
        # if gs://my-bucket/subdir exists as a subdirectory, the command:

        # gsutil cp -r dir1/dir2 gs://my-bucket/subdir

        # will create the object gs://my-bucket/subdir/dir2/a/b/c. In contrast, if
        # gs://my-bucket/subdir does not exist, this same gsutil cp command will create
        # the object gs://my-bucket/subdir/a/b/c.
        if no_target_directory or not await _is_dir(root, dst):
            target_dir = None
        else:
            target_dir = dst
            dst = None

    filters = await calc_filters(root.client, filters)
    srcs = await _expand(sources, root, glob, allow_file=True)
    if no_target_directory and len(srcs) > 1:
        raise click.UsageError(f"Extra operand after {str(srcs[1])!r}")

    file_filter = FileFilter()
    for exclude, pattern in filters:
        file_filter.append(exclude, pattern)

    show_progress = root.tty and progress

    errors = False
    for src in srcs:
        if target_dir:
            dst = target_dir / src.name
        assert dst

        progress_obj = create_storage_progress(root, show_progress)
        progress_obj.begin(src, dst)

        try:
            if src.scheme == "file" and dst.scheme == "object":
                if recursive and await _is_dir(root, src):
                    await root.client.obj.upload_dir(
                        src, dst, filter=file_filter.match, progress=progress_obj,
                    )
                else:
                    await root.client.obj.upload_file(src, dst, progress=progress_obj)
            elif src.scheme == "object" and dst.scheme == "file":
                if recursive and await _is_dir(root, src):
                    await root.client.obj.download_dir(
                        src, dst, filter=file_filter.match, progress=progress_obj,
                    )
                else:
                    await root.client.obj.download_file(src, dst, progress=progress_obj)
            else:
                raise RuntimeError(
                    f"Copy operation of the file with scheme '{src.scheme}'"
                    f" to the file with scheme '{dst.scheme}'"
                    f" is not supported"
                )
        except (OSError, ResourceNotFound, IllegalArgumentError) as error:
            log.error(f"cannot copy {src} to {dst}: {error}")
            errors = True

        progress_obj.end()

    if errors:
        sys.exit(EX_OSFILE)


async def _is_dir(root: Root, uri: URL) -> bool:
    if uri.scheme == "object":
        if uri.path.endswith("/"):
            return True
        # Check if a folder key exists. As `/` at the end makes a different key, make
        # sure we ask for one with ending slash.
        key = uri.path.lstrip("/") + "/"
        assert uri.host
        objs = await root.client.obj.list_objects(
            bucket_name=uri.host, prefix=key, recursive=False, max_keys=1
        )
        return bool(objs)

    elif uri.scheme == "file":
        path = _extract_path(uri)
        return path.is_dir()
    return False


async def _expand(
    paths: Sequence[str], root: Root, glob: bool, allow_file: bool = False
) -> List[URL]:
    uris = []
    for path in paths:
        uri = parse_obj_or_file_resource(path, root)
        if root.verbosity > 0:
            painter = get_painter(root.color, quote=True)
            curi = painter.paint(str(uri), FileStatusType.FILE)
            click.echo(f"Expand {curi}")
        uri_path = str(_extract_path(uri))
        if glob and globmodule.has_magic(uri_path):
            if uri.scheme == "object":
                assert uri.host
                if globmodule.has_magic(uri.host):
                    raise ValueError(
                        "You can not glob on bucket names. Please provide name "
                        "explicitly."
                    )
                objects = await root.client.obj.glob_objects(
                    bucket_name=uri.host, pattern=uri.path
                )
                for obj in objects:
                    uris.append(obj.uri)
            elif allow_file and uri.scheme == "file":
                for p in globmodule.iglob(uri_path, recursive=True):
                    uris.append(uri.with_path(p))
            else:
                uris.append(uri)
        else:
            uris.append(uri)
    return uris


object_storage.add_command(cp)
object_storage.add_command(ls)
object_storage.add_command(glob)
