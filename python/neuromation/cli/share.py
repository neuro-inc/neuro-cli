import logging

import click
from yarl import URL

from neuromation.client import Action, IllegalArgumentError, Permission

from .rc import Config
from .utils import command, run_async


log = logging.getLogger(__name__)


@command()
@click.argument("uri")
@click.argument("user")
@click.argument("permission", type=click.Choice(["read", "write", "manage"]))
@click.pass_obj
@run_async
async def share(cfg: Config, uri: str, user: str, permission: str) -> None:
    """
        Shares resource specified by URI to a USER with PERMISSION

        Examples:
        neuro share storage:///sample_data/ alice manage
        neuro share image:resnet50 bob read
        neuro share job:///my_job_id alice write
    """
    uri_obj = URL(uri)
    try:
        action = Action[permission.upper()]
    except KeyError as error:
        raise ValueError(
            "Resource not shared. Please specify one of read/write/manage."
        ) from error
    permission_obj = Permission.from_cli(
        username=cfg.username, uri=uri_obj, action=action
    )

    log.info(f"Using resource '{permission_obj.uri}'")

    async with cfg.make_client() as client:
        try:
            await client.users.share(user, permission_obj)
        except IllegalArgumentError as error:
            raise ValueError(
                "Resource not shared. Please verify resource-uri, user name."
            ) from error
