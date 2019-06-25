import logging

import click

from neuromation.api import DockerImageOperation, ImageNameParser
from neuromation.cli.formatters import DockerImageProgress

from .root import Root
from .utils import async_cmd, command, deprecated_quiet_option, group


log = logging.getLogger(__name__)


@group()
def image() -> None:
    """
    Container image operations.
    """


@command()
@click.argument("image_name")
@click.argument("remote_image_name", required=False)
@deprecated_quiet_option
@async_cmd()
async def push(root: Root, image_name: str, remote_image_name: str) -> None:
    """
    Push an image to platform registry.

    Remote image must be URL with image:// scheme.
    Image names can contains tag. If tags not specified 'latest' will
    be used as value.

    Examples:

    neuro push myimage
    neuro push alpine:latest image:my-alpine:production
    neuro push alpine image://myfriend/alpine:shared

    """

    parser = ImageNameParser(root.username, root.registry_url)
    local_img = parser.parse_as_docker_image(image_name)
    if remote_image_name:
        remote_img = parser.parse_as_neuro_image(remote_image_name)
    else:
        remote_img = parser.convert_to_neuro_image(local_img)

    log.debug(f"LOCAL: '{local_img}'")
    log.debug(f"REMOTE: '{remote_img}'")

    progress = DockerImageProgress.create(
        type=DockerImageOperation.PUSH,
        input_image=local_img.as_local_str(),
        output_image=remote_img.as_url_str(),
        tty=root.tty,
        quiet=root.quiet,
    )

    result_remote_image = await root.client.images.push(local_img, remote_img, progress)
    progress.close()
    click.echo(result_remote_image.as_url_str())


@command()
@click.argument("image_name")
@click.argument("local_image_name", required=False)
@deprecated_quiet_option
@async_cmd()
async def pull(root: Root, image_name: str, local_image_name: str) -> None:
    """
    Pull an image from platform registry.

    Remote image name must be URL with image:// scheme.
    Image names can contain tag.

    Examples:

    neuro pull image:myimage
    neuro pull image://myfriend/alpine:shared
    neuro pull image://username/my-alpine:production alpine:from-registry

    """

    parser = ImageNameParser(root.username, root.registry_url)
    remote_img = parser.parse_as_neuro_image(image_name)
    if local_image_name:
        local_img = parser.parse_as_docker_image(local_image_name)
    else:
        local_img = parser.convert_to_docker_image(remote_img)

    log.debug(f"REMOTE: '{remote_img}'")
    log.debug(f"LOCAL: '{local_img}'")

    progress = DockerImageProgress.create(
        type=DockerImageOperation.PULL,
        input_image=remote_img.as_url_str(),
        output_image=local_img.as_local_str(),
        tty=root.tty,
        quiet=root.quiet,
    )
    result_local_image = await root.client.images.pull(remote_img, local_img, progress)
    progress.close()
    click.echo(result_local_image.as_local_str())


@command()
@async_cmd()
async def ls(root: Root) -> None:
    """
    List images.
    """

    images = await root.client.images.ls()
    for image in images:
        click.echo(image)


image.add_command(ls)
image.add_command(push)
image.add_command(pull)
