import glob as globmodule  # avoid conflict with subcommand "glob"
import logging
import sys
from itertools import chain
from typing import List, Optional, Sequence, Tuple, Union, cast

import click
from yarl import URL

from neuromation.api import FileStatusType, IllegalArgumentError, ResourceNotFound
from neuromation.api.blob_storage import BlobListing, BucketListing, PrefixListing
from neuromation.api.file_filter import FileFilter
from neuromation.api.url_utils import _extract_path

from .const import EX_OSFILE
from .formatters import (
    BaseBlobFormatter,
    FilesSorter,
    LongBlobFormatter,
    SimpleBlobFormatter,
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
    parse_blob_or_file_resource,
    parse_blob_resource,
)


log = logging.getLogger(__name__)


@group(name="blob")
def blob_storage() -> None:
    """
    Blob storage operations.
    """


BlobListings = Union[BucketListing, BlobListing, PrefixListing]


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
    List buckets or bucket contents.
    """
    uris = [parse_blob_resource(path, root) for path in paths]

    blob_storage = root.client.blob_storage

    formatter: BaseBlobFormatter
    if format_long:
        # Similar to `ls -l`
        formatter = LongBlobFormatter(human_readable=human_readable, color=root.color)
    else:
        # Similar to `ls -1`, default for non-terminal on UNIX. We show full uris of
        # blobs, thus column formatting does not work too well.
        formatter = SimpleBlobFormatter(root.color)
    sorter = FilesSorter(sort)

    errors = False
    if not uris:
        # List Buckets instead of blobs in bucket
        buckets = await blob_storage.list_buckets()
        pager_maybe(formatter(buckets), root.tty, root.terminal_size)
    else:
        for uri in uris:
            bucket_name, key = blob_storage._extract_bucket_and_key(uri)
            short_uri = blob_storage.make_url(bucket_name, key)
            if root.verbosity > 0:
                painter = get_painter(root.color, quote=True)
                curi = painter.paint(str(short_uri), FileStatusType.DIRECTORY)
                click.echo(f"List of {curi}:")

            try:
                blobs, prefixes = await blob_storage.list_blobs(
                    bucket_name=bucket_name, prefix=key, recursive=recursive,
                )
                items = cast(Sequence[BlobListings], chain(blobs, prefixes))
            except ResourceNotFound as error:
                log.error(f"cannot access {short_uri}: {error}")
                errors = True
            else:
                items = sorted(items, key=sorter.key())
                pager_maybe(formatter(items), root.tty, root.terminal_size)

    if errors:
        sys.exit(EX_OSFILE)


@command()
@click.argument("patterns", nargs=-1, required=False)
async def glob(root: Root, patterns: Sequence[str]) -> None:
    """
    List resources that match PATTERNS.
    """
    blob_storage = root.client.blob_storage
    for pattern in patterns:
        uri = parse_blob_resource(pattern, root)
        bucket_name, pattern = blob_storage._extract_bucket_and_key(uri)
        short_uri = blob_storage.make_url(bucket_name, pattern)

        if globmodule.has_magic(bucket_name):
            raise ValueError(
                "You can not glob on bucket names. Please provide name " "explicitly."
            )

        if root.verbosity > 0:
            painter = get_painter(root.color, quote=True)
            curi = painter.paint(str(short_uri), FileStatusType.FILE)
            click.echo(f"Using pattern {curi}:")

        async for blob in blob_storage.glob_blobs(bucket_name, pattern):
            click.echo(blob.uri)


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
    Simple utility to copy files and directories into and from Blob Storage.
    Either SOURCES or DESTINATION should have `blob://` scheme.
    If scheme is omitted, file:// scheme is assumed. It is currently not possible to
    copy files between Blob Storage (`blob://`) destination, nor with `storage://`
    scheme paths.
    Use `/dev/stdin` and `/dev/stdout` file names to upload a file from standard input
    or output to stdout.
    File permissions, modification times and other attributes will not be passed to
    Blob Storage metadata during upload.
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
        target_dir = parse_blob_or_file_resource(target_directory, root)
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
        dst = parse_blob_or_file_resource(destination, root)

        # From gsutil:
        #
        # There's an additional wrinkle when working with subdirectories: the resulting
        # names depend on whether the destination subdirectory exists. For example,
        # if gs://my-bucket/subdir exists as a subdirectory, the command:

        # gsutil cp -r dir1/dir2 gs://my-bucket/subdir

        # will create the blob gs://my-bucket/subdir/dir2/a/b/c. In contrast, if
        # gs://my-bucket/subdir does not exist, this same gsutil cp command will create
        # the blob gs://my-bucket/subdir/a/b/c.
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
        log.debug("%s %s", "Exclude" if exclude else "Include", pattern)
        file_filter.append(exclude, pattern)

    show_progress = root.tty and progress

    errors = False
    for src in srcs:
        # `src.name` will return empty string if URL has trailing slash, ie.:
        # `neuro blob cp data/ blob:my_bucket` -> dst == blob:my_bucket/file.txt
        # `neuro blob cp data blob:my_bucket` -> dst == blob:my_bucket/data/file.txt
        # `neuro blob cp blob:my_bucket data` -> dst == data/my_bucket/file.txt
        # `neuro blob cp blob:my_bucket/ data` -> dst == data/file.txt
        if target_dir:
            dst = target_dir / src.name
        assert dst

        progress_blob = create_storage_progress(root, show_progress)
        progress_blob.begin(src, dst)

        try:
            if src.scheme == "file" and dst.scheme == "blob":
                if recursive and await _is_dir(root, src):
                    await root.client.blob_storage.upload_dir(
                        src, dst, filter=file_filter.match, progress=progress_blob,
                    )
                else:
                    await root.client.blob_storage.upload_file(
                        src, dst, progress=progress_blob
                    )
            elif src.scheme == "blob" and dst.scheme == "file":
                if recursive and await _is_dir(root, src):
                    await root.client.blob_storage.download_dir(
                        src, dst, filter=file_filter.match, progress=progress_blob,
                    )
                else:
                    await root.client.blob_storage.download_file(
                        src, dst, progress=progress_blob
                    )
            else:
                raise RuntimeError(
                    f"Copy operation of the file with scheme '{src.scheme}'"
                    f" to the file with scheme '{dst.scheme}'"
                    f" is not supported"
                )
        except (OSError, ResourceNotFound, IllegalArgumentError) as error:
            log.error(f"cannot copy {src} to {dst}: {error}")
            errors = True

        progress_blob.end()

    if errors:
        sys.exit(EX_OSFILE)


async def _is_dir(root: Root, uri: URL) -> bool:
    if uri.scheme == "blob":
        return await root.client.blob_storage._is_dir(uri)

    elif uri.scheme == "file":
        path = _extract_path(uri)
        return path.is_dir()
    return False


async def _expand(
    paths: Sequence[str], root: Root, glob: bool, allow_file: bool = False
) -> List[URL]:
    uris = []
    for path in paths:
        uri = parse_blob_or_file_resource(path, root)
        if root.verbosity > 0:
            painter = get_painter(root.color, quote=True)
            curi = painter.paint(str(uri), FileStatusType.FILE)
            click.echo(f"Expand {curi}")
        uri_path = str(_extract_path(uri))
        if glob and globmodule.has_magic(uri_path):
            if uri.scheme == "blob":
                bucket_name, key = root.client.blob_storage._extract_bucket_and_key(uri)
                if globmodule.has_magic(bucket_name):
                    raise ValueError(
                        "You can not glob on bucket names. Please provide name "
                        "explicitly."
                    )
                async for blob in root.client.blob_storage.glob_blobs(
                    bucket_name=bucket_name, pattern=key
                ):
                    uris.append(blob.uri)
            elif allow_file and uri.scheme == "file":
                for p in globmodule.iglob(uri_path, recursive=True):
                    uris.append(uri.with_path(p))
            else:
                uris.append(uri)
        else:
            uris.append(uri)
    return uris


blob_storage.add_command(cp)
blob_storage.add_command(ls)
blob_storage.add_command(glob)
