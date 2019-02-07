import logging
import sys

import click
from yarl import URL

# TODO(asvetlov): rename the class to avoid the namig conflict
from neuromation.client.images import Image

from .command_spinner import SpinnerBase
from .rc import Config
from .utils import command, group, run_async


log = logging.getLogger(__name__)


@group()
def image() -> None:
    """
    Container image operations.
    """


@command()
@click.argument("image_name")
@click.argument("remote_image_name", required=False)
@click.pass_obj
@run_async
async def push(cfg: Config, image_name: str, remote_image_name: str) -> None:
    """
    Push an image to platform registry.

    Remote image must be URL with image:// scheme.
    Image names can contains tag. If tags not specified 'latest' will
    be used as value.

    Examples:

    neuro image push myimage
    neuro image push alpine:latest image:my-alpine:production
    neuro image push alpine image://myfriend/alpine:shared

    """

    username = cfg.username

    local_image = remote_image = Image.from_local(image_name, username)
    if remote_image_name:
        remote_image = Image.from_url(URL(remote_image_name), username)

    log.info(f"Using remote image '{remote_image.url}'")
    log.info(f"Using local image '{local_image.url}'")

    spinner = SpinnerBase.create_spinner(sys.stdout.isatty(), "Pushing image {}  ")

    async with cfg.make_client() as client:
        result_remote_image = await client.images.push(
            local_image, remote_image, spinner
        )
        click.echo(result_remote_image.url)


@command()
@click.argument("image_name")
@click.argument("local_image_name", required=False)
@click.pass_obj
@run_async
async def pull(cfg: Config, image_name: str, local_image_name: str) -> None:
    """
    Pull an image from platform registry.

    Remote image name must be URL with image:// scheme.
    Image names can contain tag.

    Examples:

    neuro image pull image:myimage
    neuro image pull image://myfriend/alpine:shared
    neuro image pull image://username/my-alpine:production alpine:from-registry

    """

    username = cfg.username

    remote_image = local_image = Image.from_url(URL(image_name), username)
    if local_image_name:
        local_image = Image.from_local(local_image_name, username)
    log.info(f"Using remote image '{remote_image.url}'")
    log.info(f"Using local image '{local_image.url}'")

    spinner = SpinnerBase.create_spinner(sys.stdout.isatty(), "Pulling image {}  ")

    async with cfg.make_client() as client:
        result_local_image = await client.images.pull(
            remote_image, local_image, spinner
        )
        click.echo(result_local_image.local)


@command()
@click.pass_obj
@run_async
async def ls(cfg: Config) -> None:
    """
    List images.
    """

    async with cfg.make_client() as client:
        images = await client.images.ls()
        for image in images:
            click.echo(image)


image.add_command(ls)
image.add_command(push)
image.add_command(pull)
