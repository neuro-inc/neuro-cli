from datetime import timedelta
from typing import Optional, Sequence

from .formatters.disks import (
    BaseDisksFormatter,
    DiskFormatter,
    DisksFormatter,
    SimpleDisksFormatter,
)
from .formatters.utils import URIFormatter, uri_formatter
from .parse_utils import parse_memory
from .root import Root
from .utils import argument, calc_life_span, command, group, option


DEFAULT_DISK_LIFE_SPAN = "1d"


@group()
def disk() -> None:
    """
    Operations with disks.
    """


@command()
@option("--full-uri", is_flag=True, help="Output full disk URI.")
@option("--long-format", is_flag=True, help="Output all info about disk.")
async def ls(root: Root, full_uri: bool, long_format: bool) -> None:
    """
    List disks.
    """
    if root.quiet:
        disks_fmtr: BaseDisksFormatter = SimpleDisksFormatter()
    else:
        if full_uri:
            uri_fmtr: URIFormatter = str
        else:
            uri_fmtr = uri_formatter(
                username=root.client.username, cluster_name=root.client.cluster_name
            )
        disks_fmtr = DisksFormatter(uri_fmtr, long_format=long_format)

    disks = []
    async for disk in root.client.disks.list():
        disks.append(disk)

    with root.pager():
        root.print(disks_fmtr(disks))


@command()
@argument("storage")
@option(
    "--life-span",
    type=str,
    metavar="TIMEDELTA",
    help=(
        "Optional disk lifetime limit after last usage "
        "in the format '1d2h3m4s' (some parts may be missing). "
        "Set '0' to disable. Default value '1d' can be changed "
        "in the user config."
    ),
)
async def create(root: Root, storage: str, life_span: Optional[str] = None) -> None:
    """
    Create a disk with at least storage amount STORAGE.

    To specify the amount, you can use the following suffixes: "kKMGTPEZY"
    To use decimal quantities, append "b" or "B". For example:
    - 1K or 1k is 1024 bytes
    - 1Kb or 1KB is 1000 bytes
    - 20G is 20 * 2 ^ 30 bytes
    - 20Gb or 20GB is 20.000.000.000 bytes

    Note that server can have big granularity (for example, 1G)
    so it will possibly round-up the amount you requested.

    Examples:

      neuro disk create 10G
      neuro disk create 500M
    """
    life_span_seconds = await calc_life_span(
        root.client, life_span, DEFAULT_DISK_LIFE_SPAN, "disk"
    )
    disk_life_span = None
    if life_span_seconds:
        disk_life_span = timedelta(seconds=life_span_seconds)

    disk = await root.client.disks.create(
        parse_memory(storage), life_span=disk_life_span
    )
    disk_fmtr = DiskFormatter(str)
    with root.pager():
        root.print(disk_fmtr(disk))


@command()
@argument("disk_id")
@option("--full-uri", is_flag=True, help="Output full disk URI.")
async def get(root: Root, disk_id: str, full_uri: bool) -> None:
    """
    Get disk DISK_ID.
    """
    disk = await root.client.disks.get(disk_id)
    if full_uri:
        uri_fmtr: URIFormatter = str
    else:
        uri_fmtr = uri_formatter(
            username=root.client.username, cluster_name=root.client.cluster_name
        )
    disk_fmtr = DiskFormatter(uri_fmtr)
    with root.pager():
        root.print(disk_fmtr(disk))


@command()
@argument("disk_ids", nargs=-1, required=True)
async def rm(root: Root, disk_ids: Sequence[str]) -> None:
    """
    Remove disk DISK_ID.
    """
    for disk_id in disk_ids:
        await root.client.disks.rm(disk_id)
        if root.verbosity > 0:
            root.print(f"Disk with id '{disk_id}' was successfully removed.")


disk.add_command(ls)
disk.add_command(create)
disk.add_command(get)
disk.add_command(rm)
