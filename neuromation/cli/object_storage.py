import logging
from typing import List, Sequence

import click

from neuromation.api.object_storage import ObjStatus

from .formatters import (
    BaseFilesFormatter,
    LongFilesFormatter,
    SimpleFilesFormatter,
    VerticalColumnsFilesFormatter,
)
from .root import Root
from .utils import command, group, option, pager_maybe, parse_obj_resource


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


object_storage.add_command(ls)
