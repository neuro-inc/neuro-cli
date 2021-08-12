import glob as globmodule  # avoid conflict with subcommand "glob"
import logging
import sys
from typing import List, Optional, Sequence, Tuple

import click
from rich.text import Text
from yarl import URL

from neuro_sdk import FileStatusType, IllegalArgumentError, ResourceNotFound
from neuro_sdk.file_filter import FileFilter
from neuro_sdk.url_utils import _extract_path

from neuro_cli.formatters.utils import URIFormatter, uri_formatter

from .const import EX_OSFILE
from .formatters.blob_storage import (
    BaseBlobFormatter,
    LongBlobFormatter,
    SimpleBlobFormatter,
)
from .formatters.storage import create_storage_progress, get_painter
from .root import Root
from .storage import calc_filters, calc_ignore_file_names, filter_option
from .utils import (
    command,
    group,
    option,
    parse_blob_or_file_resource,
    parse_blob_resource,
)

log = logging.getLogger(__name__)


@group(name="blob")
def blob_storage() -> None:
    """
    Blob storage operations.
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
    "-r",
    "--recursive",
    is_flag=True,
    help="List all keys under the URL path provided, not just 1 level depths.",
)
@option("--full-uri", is_flag=True, help="Output full bucket URI.")
async def ls(
    root: Root,
    paths: Sequence[str],
    human_readable: bool,
    format_long: bool,
    recursive: bool,
    full_uri: bool,
) -> None:
    """
    List buckets or bucket contents.
    """
    uris = [parse_blob_resource(path, root) for path in paths]

    formatter: BaseBlobFormatter
    if full_uri:
        uri_fmtr: URIFormatter = str
    else:
        uri_fmtr = uri_formatter(
            username=root.client.username,
            cluster_name=root.client.cluster_name,
        )
    if format_long:
        # Similar to `ls -l`
        formatter = LongBlobFormatter(
            human_readable=human_readable, color=root.color, uri_formatter=uri_fmtr
        )
    else:
        # Similar to `ls -1`, default for non-terminal on UNIX. We show full uris of
        # blobs, thus column formatting does not work too well.
        formatter = SimpleBlobFormatter(root.color, uri_fmtr)

    errors = False
    if not uris:
        # List Buckets instead of blobs in bucket

        with root.pager():
            async with root.client.buckets.list() as bucket_it:
                async for bucket in bucket_it:
                    root.print(formatter(bucket))
    else:
        for uri, path in zip(uris, paths):
            if root.verbosity > 0:
                painter = get_painter(root.color)
                uri_text = painter.paint(str(path), FileStatusType.DIRECTORY)
                root.print(Text.assemble("List of ", uri_text, ":"))

            with root.pager():
                async with root.client.buckets.list_blobs(
                    uri=uri,
                    recursive=recursive,
                ) as blobs_it:
                    async for entry in blobs_it:
                        root.print(formatter(entry))
    if errors:
        sys.exit(EX_OSFILE)


@command()
@option("--full-uri", is_flag=True, help="Output full bucket URI.")
@click.argument("patterns", nargs=-1, required=False)
async def glob(root: Root, full_uri: bool, patterns: Sequence[str]) -> None:
    """
    List resources that match PATTERNS.
    """
    if full_uri:
        uri_fmtr: URIFormatter = str
    else:
        uri_fmtr = uri_formatter(
            username=root.client.username,
            cluster_name=root.client.cluster_name,
        )
    for pattern in patterns:

        uri = parse_blob_resource(pattern, root)

        if root.verbosity > 0:
            painter = get_painter(root.color)
            uri_text = painter.paint(pattern, FileStatusType.FILE)
            root.print(Text.assemble("Using pattern ", uri_text, ":"))

        async with root.client.buckets.glob_blobs(uri=uri) as blobs_it:
            async for entry in blobs_it:
                root.print(uri_fmtr(entry.uri))


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
@option(
    "-u",
    "--update",
    is_flag=True,
    help="Copy only when the SOURCE file is newer than the destination file "
    "or when the destination file is missing.",
)
@option(
    "--continue",
    "continue_",
    is_flag=True,
    help="Continue copying partially-copied files. "
    "Only for copying from Blob Storage.",
)
@filter_option(
    "--exclude",
    "filters",
    flag_value=True,
    help=("Exclude files and directories that match the specified pattern."),
)
@filter_option(
    "--include",
    "filters",
    flag_value=False,
    help=("Don't exclude files and directories that match the specified pattern."),
)
@option(
    "--exclude-from-files",
    metavar="FILES",
    default=None,
    help=(
        "A list of file names that contain patterns for exclusion files "
        "and directories. Used only for uploading. "
        "The default can be changed using the storage.cp-exclude-from-files "
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
    update: bool,
    continue_: bool,
    filters: Optional[Tuple[Tuple[bool, str], ...]],
    exclude_from_files: str,
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

    Any number of --exclude and --include options can be passed.  The
    filters that appear later in the command take precedence over filters
    that appear earlier in the command.  If neither --exclude nor
    --include options are specified the default can be changed using the
    storage.cp-exclude configuration variable documented in
    "neuro help user-config".

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

    ignore_file_names = await calc_ignore_file_names(root.client, exclude_from_files)
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
        try:
            with progress_blob.begin(src, dst):
                if src.scheme == "file" and dst.scheme == "blob":
                    if continue_:
                        raise click.UsageError(
                            "Option --continue is not supported for copying to "
                            "Blob Storage"
                        )

                    if recursive and await _is_dir(root, src):
                        await root.client.buckets.upload_dir(
                            src,
                            dst,
                            update=update,
                            filter=file_filter.match,
                            ignore_file_names=frozenset(ignore_file_names),
                            progress=progress_blob,
                        )
                    else:
                        await root.client.buckets.upload_file(
                            src, dst, update=update, progress=progress_blob
                        )
                elif src.scheme == "blob" and dst.scheme == "file":
                    if recursive and await _is_dir(root, src):
                        await root.client.buckets.download_dir(
                            src,
                            dst,
                            continue_=continue_,
                            update=update,
                            filter=file_filter.match,
                            progress=progress_blob,
                        )
                    else:
                        await root.client.buckets.download_file(
                            src,
                            dst,
                            continue_=continue_,
                            update=update,
                            progress=progress_blob,
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

    if errors:
        sys.exit(EX_OSFILE)


async def _is_dir(root: Root, uri: URL) -> bool:
    if uri.scheme == "blob":
        return await root.client.buckets.blob_is_dir(uri)

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
            painter = get_painter(root.color)
            uri_text = painter.paint(str(uri), FileStatusType.FILE)
            root.print(Text.assemble("Expand", uri_text))

        if glob and globmodule.has_magic(uri.path):
            if uri.scheme == "blob":
                async with root.client.buckets.glob_blobs(uri) as blob_iter:
                    async for blob in blob_iter:
                        uris.append(blob.uri)
            elif allow_file and uri.scheme == "file":
                uri_path = str(_extract_path(uri))
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
