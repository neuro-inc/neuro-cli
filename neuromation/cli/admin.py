from typing import Optional

import click

from neuromation.api.admin import _ClusterUserRoleType

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
    pager_maybe(
        fmt(clusters), root.tty, root.terminal_size,
    )


@command()
@click.argument("cluster_name", required=True, type=str)
@click.argument("user_name", required=True, type=str)
@click.argument(
    "role",
    required=False,
    default="user",
    type=click.Choice(list(_ClusterUserRoleType)),
)
@async_cmd()
async def add_cluster_user(
    root: Root, cluster_name: str, user_name: str, role: str
) -> None:
    """
    Add user access to specified cluster with one of 3 roles: admin, manager or user
    """
    await root.client._admin.add_cluster_user(cluster_name, user_name, role)
    if not root.quiet:
        click.echo(
            f"Added {click.style(user_name, bold=True)} to cluster "
            f"{click.style(cluster_name, bold=True)} as {click.style(role, bold=True)}"
        )


@command()
@click.argument("cluster_name", required=True, type=str)
@click.argument("user_name", required=True, type=str)
@async_cmd()
async def remove_cluster_user(root: Root, cluster_name: str, user_name: str) -> None:
    """
    Remove user access from the cluster
    """
    await root.client._admin.remove_cluster_user(cluster_name, user_name)
    if not root.quiet:
        click.echo(
            f"Removed {click.style(user_name, bold=True)} from cluster "
            f"{click.style(cluster_name, bold=True)}"
        )


admin.add_command(get_cluster_users)
admin.add_command(add_cluster_user)
admin.add_command(remove_cluster_user)
