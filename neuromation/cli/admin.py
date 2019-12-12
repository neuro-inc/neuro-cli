import io
from typing import Optional

import click
import yaml

from .formatters import ClustersFormatter, ClusterUserFormatter
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
    pager_maybe(
        fmt(clusters), root.tty, root.terminal_size,
    )


@command()
@async_cmd()
async def get_clusters(root: Root) -> None:
    """
    Print the list of available clusters.
    """
    fmt = ClustersFormatter()
    clusters = await root.client._admin.list_clusters()
    pager_maybe(
        fmt(clusters.values()), root.tty, root.terminal_size,
    )


@command()
@click.argument("cluster_name", required=True, type=str)
@click.argument("config", required=True, type=click.File(encoding="utf8", lazy=False))
@async_cmd()
async def add_cluster(root: Root, cluster_name: str, config: io.TextIOBase) -> None:
    """
    Create a new cluster and start its provisioning
    """
    if not root.quiet:
        click.echo(f"Creating cluster {cluster_name}")
    config_dict = yaml.safe_load(config)
    await root.client._admin.add_cluster(cluster_name, config_dict)
    if not root.quiet:
        click.echo(f"Done")


admin.add_command(get_cluster_users)
admin.add_command(get_clusters)
admin.add_command(add_cluster)
