import logging
import sys

import click

from neuromation.client import ImageParser

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

    parser = ImageParser(cfg.username, cfg.registry_url)
    local_img = parser.parse_as_docker_image(image_name)
    remote_img = (
        parser.parse_as_neuro_image(remote_image_name)
        if remote_image_name
        else parser.convert_to_neuro_image(local_img)
    )

    log.info(f"Using local image '{local_img.as_local_str()}'")
    log.info(f"Using remote image '{remote_img.as_url_str()}'")
    log.debug(f"LOCAL: '{local_img}'")
    log.debug(f"REMOTE: '{remote_img}'")

    spinner = SpinnerBase.create_spinner(sys.stdout.isatty(), "Pushing image {}  ")

    async with cfg.make_client() as client:
        result_remote_image = await client.images.push(local_img, remote_img, spinner)
        click.echo(result_remote_image.as_url_str())


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

    parser = ImageParser(cfg.username, cfg.registry_url)
    remote_img = parser.parse_as_neuro_image(image_name)
    local_img = (
        parser.parse_as_docker_image(local_image_name)
        if local_image_name
        else parser.convert_to_docker_image(remote_img)
    )

    log.info(f"Using remote image '{remote_img.as_url_str()}'")
    log.info(f"Using local image '{local_img.as_local_str()}'")
    log.debug(f"REMOTE: '{remote_img}'")
    log.debug(f"LOCAL: '{local_img}'")

    spinner = SpinnerBase.create_spinner(sys.stdout.isatty(), "Pulling image {}  ")

    async with cfg.make_client() as client:
        result_local_image = await client.images.pull(remote_img, local_img, spinner)
        click.echo(result_local_image.as_local_str())


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
