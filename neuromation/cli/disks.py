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
async def ls(root: Root, full_uri: bool) -> None:
    """
    List disks.
    """

    if full_uri:
        uri_fmtr: URIFormatter = str
    else:
        uri_fmtr = uri_formatter(
            username=root.client.username, cluster_name=root.client.cluster_name
        )
    disks_fmtr = DisksFormatter(uri_fmtr)

    disks = []
    async for disk in root.client.disks.list():
        disks.append(disk)

    pager_maybe(disks_fmtr(disks), root.tty, root.terminal_size)


@command()
@argument("storage")
async def create(root: Root, storage: str) -> None:
    """
    Create disk with storage amount STORAGE.

    Examples:

      neuro disk create 10Gi
      neuro disk create 500Mi
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
