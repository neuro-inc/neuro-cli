from typing import Optional

import click

from .formatters import ClusterUserFormatter
from .root import Root
from .utils import async_cmd, command, group, pager_maybe


@group()
def admin() -> None:
    """Cluster administration commands."""


@command()
@click.argument("cluster_name", required=False, default=None, type=str)
@async_cmd()
async def get_cluster_users(root: Root, cluster_name: Optional[str]) -> None:
    """
    Print the list of all users in the cluster with their assigned role
    """
    fmt = ClusterUserFormatter()
    clusters = await root.client._admin.list_cluster_users(cluster_name)
    pager_maybe(fmt(clusters), root.tty, root.terminal_size)


admin.add_command(get_cluster_users)
