import logging

import click

from neuromation.client import Permission

from .rc import Config
from .utils import (
    async_cmd,
    command,
    parse_permission_action,
    parse_resource_for_sharing,
)


log = logging.getLogger(__name__)


@command()
@click.argument("uri")
@click.argument("user")
@click.argument("permission", type=click.Choice(["read", "write", "manage"]))
@async_cmd
async def share(cfg: Config, uri: str, user: str, permission: str) -> None:
    """
        Shares resource specified by URI to a USER with PERMISSION

        Examples:
        neuro share storage:///sample_data/ alice manage
        neuro share image:resnet50 bob read
        neuro share job:///my_job_id alice write
    """
    try:
        uri_obj = parse_resource_for_sharing(uri, cfg)
        action_obj = parse_permission_action(permission)
        permission_obj = Permission.from_cli(
            username=cfg.username, uri=uri_obj, action=action_obj
        )
        log.info(f"Using resource '{permission_obj.uri}'")

        async with cfg.make_client() as client:
            await client.users.share(user, permission_obj)

    except ValueError as e:
        raise ValueError(f"Could not share resource '{uri}': {e}") from e
