import logging
from typing import Optional

import click

from neuromation.api import Permission
from neuromation.api.users import uri_from_cli

from .root import Root
from .utils import (
    async_cmd,
    command,
    group,
    parse_permission_action,
    parse_resource_for_sharing,
)


log = logging.getLogger(__name__)


@group()
def acl() -> None:
    """
    ACL operations.
    """


@command()
@click.argument("uri")
@click.argument("user")
@click.argument("permission", type=click.Choice(["read", "write", "manage"]))
@async_cmd()
async def grant(root: Root, uri: str, user: str, permission: str) -> None:
    """
        Shares resource specified by URI to a USER with PERMISSION

        Examples:
        neuro acl grant storage:///sample_data/ alice manage
        neuro acl grant image:resnet50 bob read
        neuro acl grant job:///my_job_id alice write
    """
    try:
        uri_obj = parse_resource_for_sharing(uri, root)
        action_obj = parse_permission_action(permission)
        permission_obj = Permission.from_cli(
            username=root.username, uri=uri_obj, action=action_obj
        )
        log.info(f"Using resource '{permission_obj.uri}'")

        await root.client.users.share(user, permission_obj)

    except ValueError as e:
        raise ValueError(f"Could not share resource '{uri}': {e}") from e


@command()
@click.argument("uri")
@click.argument("user")
@async_cmd()
async def revoke(root: Root, uri: str, user: str) -> None:
    """
        Revoke from a USER permissions for previously shared resource specified by URI

        Examples:
        neuro acl revoke storage:///sample_data/ alice
        neuro acl revoke image:resnet50 bob
        neuro acl revoke job:///my_job_id alice
    """
    try:
        uri_obj = parse_resource_for_sharing(uri, root)
        uri_obj = uri_from_cli(username=root.username, uri=uri_obj)
        log.info(f"Using resource '{uri_obj}'")

        await root.client.users.revoke(user, uri_obj)

    except ValueError as e:
        raise ValueError(f"Could not unshare resource '{uri}': {e}") from e


@command()
@click.argument("scheme", required=False, default=None)
@click.option(
    "--shared",
    is_flag=True,
    default=False,
    help="Output the resources shared by the user",
)
@async_cmd()
async def list(root: Root, scheme: Optional[str], shared: bool) -> None:
    """
        List resource available to a USER or shared by a USER

        Examples:
        neuro acl list
        neuro acl list storage
        neuro acl list --shared
        neuro acl list --shared image
    """
    if not shared:
        for uri, action in sorted(await root.client.users.list(root.username, scheme)):
            print(uri, action.value)
    else:
        for user, uri, action in sorted(
            await root.client.users.list_shared(root.username, scheme)
        ):
            print(uri, action.value, user)


acl.add_command(grant)
acl.add_command(revoke)
acl.add_command(list)
