from datetime import timedelta
from typing import Optional, Sequence

from neuro_cli.click_types import CLUSTER, DISK, DISK_NAME
from neuro_cli.formatters.utils import get_datetime_formatter
from neuro_cli.utils import resolve_disk

from .formatters.disks import (
    BaseDisksFormatter,
    DiskFormatter,
    DisksFormatter,
    SimpleDisksFormatter,
)
from .formatters.utils import URIFormatter, uri_formatter
from .parse_utils import parse_memory
from .root import Root
from .utils import argument, calc_timeout_unused, command, group, option

DEFAULT_DISK_LIFE_SPAN = "1d"


@group()
def disk() -> None:
    """
    Operations with disks.
    """


@command()
@option(
    "--cluster",
    type=CLUSTER,
    help="Look on a specified cluster (the current cluster by default).",
)
@option("--full-uri", is_flag=True, help="Output full disk URI.")
@option("--long-format", is_flag=True, help="Output all info about disk.")
async def ls(
    root: Root, full_uri: bool, long_format: bool, cluster: Optional[str]
) -> None:
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
                username=root.client.username,
                cluster_name=cluster or root.client.cluster_name,
            )
        disks_fmtr = DisksFormatter(
            uri_fmtr,
            long_format=long_format,
            datetime_formatter=get_datetime_formatter(root.iso_datetime_format),
        )

    disks = []
    with root.status("Fetching disks") as status:
        async with root.client.disks.list(cluster_name=cluster) as it:
            async for disk in it:
                disks.append(disk)
                status.update(f"Fetching disks ({len(disks)} loaded)")

    with root.pager():
        root.print(disks_fmtr(disks))


@command()
@argument("storage")
@option(
    "--cluster",
    type=CLUSTER,
    help="Perform in a specified cluster (the current cluster by default).",
)
@option(
    "--timeout-unused",
    type=str,
    metavar="TIMEDELTA",
    help=(
        "Optional disk lifetime limit after last usage "
        "in the format '1d2h3m4s' (some parts may be missing). "
        "Set '0' to disable. Default value '1d' can be changed "
        "in the user config."
    ),
)
@option(
    "--name",
    type=DISK_NAME,
    metavar="NAME",
    help="Optional disk name",
    default=None,
)
async def create(
    root: Root,
    storage: str,
    timeout_unused: Optional[str] = None,
    name: Optional[str] = None,
    cluster: Optional[str] = None,
) -> None:
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
    timeout_unused_seconds = await calc_timeout_unused(
        root.client, timeout_unused, DEFAULT_DISK_LIFE_SPAN, "disk"
    )
    disk_timeout_unused = None
    if timeout_unused_seconds:
        disk_timeout_unused = timedelta(seconds=timeout_unused_seconds)

    disk = await root.client.disks.create(
        parse_memory(storage),
        timeout_unused=disk_timeout_unused,
        name=name,
        cluster_name=cluster,
    )
    disk_fmtr = DiskFormatter(
        str, datetime_formatter=get_datetime_formatter(root.iso_datetime_format)
    )
    with root.pager():
        root.print(disk_fmtr(disk))


@command()
@option(
    "--cluster",
    type=CLUSTER,
    help="Look on a specified cluster (the current cluster by default).",
)
@argument("disk", type=DISK)
@option("--full-uri", is_flag=True, help="Output full disk URI.")
async def get(root: Root, cluster: Optional[str], disk: str, full_uri: bool) -> None:
    """
    Get disk DISK_ID.
    """
    disk_id = await resolve_disk(disk, client=root.client, cluster_name=cluster)
    disk_obj = await root.client.disks.get(disk_id, cluster_name=cluster)
    if full_uri:
        uri_fmtr: URIFormatter = str
    else:
        uri_fmtr = uri_formatter(
            username=root.client.username,
            cluster_name=cluster or root.client.cluster_name,
        )
    disk_fmtr = DiskFormatter(
        uri_fmtr, datetime_formatter=get_datetime_formatter(root.iso_datetime_format)
    )
    with root.pager():
        root.print(disk_fmtr(disk_obj))


@command()
@option(
    "--cluster",
    type=CLUSTER,
    help="Perform on a specified cluster (the current cluster by default).",
)
@argument("disks", type=DISK, nargs=-1, required=True)
async def rm(root: Root, cluster: Optional[str], disks: Sequence[str]) -> None:
    """
    Remove disk DISK_ID.
    """
    for disk in disks:
        disk_id = await resolve_disk(disk, client=root.client, cluster_name=cluster)
        await root.client.disks.rm(disk_id, cluster_name=cluster)
        if root.verbosity >= 0:
            root.print(f"Disk with id '{disk_id}' was successfully removed.")


disk.add_command(ls)
disk.add_command(create)
disk.add_command(get)
disk.add_command(rm)
