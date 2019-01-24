import click
from yarl import URL

from neuromation.clientv2 import Action, IllegalArgumentError, Permission

from . import rc
from .utils import Context, run_async


@click.command()
@click.argument('uri')
@click.argument('user')
@click.argument('permission', type=click.Choice(['read', 'write', 'manage']))
@click.pass_obj
@run_async
async def share(ctx: Context, uri: str, user: str, permission: str) -> None:
    """
        Shares resource specified by URI to a USER with PERMISSION

        Examples:
        neuro share storage:///sample_data/ alice manage
        neuro share image:resnet50 bob read
        neuro share job:///my_job_id alice write
    """
    uri = URL(uri)
    try:
        action = Action[permission.upper()]
    except KeyError as error:
        raise ValueError(
            "Resource not shared. Please specify one of read/write/manage."
        ) from error
    config = rc.ConfigFactory.load()
    platform_user_name = config.get_platform_user_name()
    permission = Permission.from_cli(
        username=platform_user_name, uri=uri, action=action
    )

    async with ctx.make_client() as client:
        try:
            await client.users.share(user, permission)
        except IllegalArgumentError as error:
            raise ValueError(
                "Resource not shared. Please verify resource-uri, user name."
            ) from error
