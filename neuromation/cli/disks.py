from .formatters.disks import DiskFormatter, DisksFormatter
from .formatters.utils import URIFormatter, uri_formatter
from .parse_utils import parse_memory
from .root import Root
from .utils import argument, command, group, option, pager_maybe


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

    pager_maybe(disks_fmtr(disks), root.tty, root.terminal_size)


@command()
@argument("storage")
async def create(root: Root, storage: str) -> None:
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
    disk = await root.client.disks.create(parse_memory(storage))
    disk_fmtr = DiskFormatter(str)
    pager_maybe(disk_fmtr(disk), root.tty, root.terminal_size)


@command()
@argument("disk_id")
async def get(root: Root, disk_id: str) -> None:
    """
    Get disk DISK_ID.
    """
    disk = await root.client.disks.get(disk_id)
    disk_fmtr = DiskFormatter(str)
    pager_maybe(disk_fmtr(disk), root.tty, root.terminal_size)


@command()
@argument("disk_id")
async def rm(root: Root, disk_id: str) -> None:
    """
    Remove disk DISK_ID.
    """

    await root.client.disks.rm(disk_id)


disk.add_command(ls)
disk.add_command(create)
disk.add_command(get)
disk.add_command(rm)
