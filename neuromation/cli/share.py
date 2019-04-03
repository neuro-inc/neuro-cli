import logging

import click
from yarl import URL

from neuromation.client import Action, ImageNameParser, Permission

from .rc import Config
from .utils import async_cmd, command


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
        # parse images by ImageNameParser, all other resources -- by yaml.URL
        if uri.startswith("image:"):
            parser = ImageNameParser(cfg.username, cfg.registry_url)
            if parser.has_tag(uri):
                raise ValueError(
                    f"Invalid image '{uri}': tags are not allowed for resource sharing"
                )
            image = parser.parse_as_docker_image(uri)
            uri_obj = URL(image.as_url_str())
        else:
            uri_obj = URL(uri)

        try:
            action = Action[permission.upper()]
        except KeyError:
            valid_actions = ", ".join([a.value for a in Action])
            raise ValueError(
                f"invalid permission '{permission}', allowed values: {valid_actions}"
            )
        permission_obj = Permission.from_cli(
            username=cfg.username, uri=uri_obj, action=action
        )

        log.info(f"Using resource '{permission_obj.uri}'")

        async with cfg.make_client() as client:
            await client.users.share(user, permission_obj)

    except ValueError as e:
        raise ValueError(f"Could not share resource '{uri}': {e}") from e
