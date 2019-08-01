import contextlib
import logging
from typing import Optional

import click

from neuromation.api import LocalImage, RemoteImage
from neuromation.cli.formatters import DockerImageProgress

from .root import Root
from .utils import (
    RemoteTaglessImageType,
    async_cmd,
    command,
    deprecated_quiet_option,
    group,
)


log = logging.getLogger(__name__)


@group()
def image() -> None:
    """
    Container image operations.
    """


@command()
@click.argument("local_image")
@click.argument("remote_image", required=False)
@deprecated_quiet_option
@async_cmd()
async def push(root: Root, local_image: str, remote_image: Optional[str]) -> None:
    """
    Push an image to platform registry.

    Remote image must be URL with image:// scheme.
    Image names can contain tag. If tags not specified 'latest' will
    be used as value.

    Examples:

    neuro push myimage
    neuro push alpine:latest image:my-alpine:production
    neuro push alpine image://myfriend/alpine:shared

    """

    progress = DockerImageProgress.create(tty=root.tty, quiet=root.quiet)
    local_obj = root.client.parse.local_image(local_image)
    if remote_image is not None:
        remote_obj: Optional[RemoteImage] = root.client.parse.remote_image(remote_image)
    else:
        remote_obj = None
    with contextlib.closing(progress):
        result_remote_image = await root.client.images.push(
            local_obj, remote_obj, progress=progress
        )
    click.echo(result_remote_image)


@command()
@click.argument("remote_image")
@click.argument("local_image", required=False)
@deprecated_quiet_option
@async_cmd()
async def pull(root: Root, remote_image: str, local_image: Optional[str]) -> None:
    """
    Pull an image from platform registry.

    Remote image name must be URL with image:// scheme.
    Image names can contain tag.

    Examples:

    neuro pull image:myimage
    neuro pull image://myfriend/alpine:shared
    neuro pull image://username/my-alpine:production alpine:from-registry

    """

    progress = DockerImageProgress.create(tty=root.tty, quiet=root.quiet)
    remote_obj = root.client.parse.remote_image(remote_image)
    if local_image is not None:
        local_obj: Optional[LocalImage] = root.client.parse.local_image(local_image)
    else:
        local_obj = None
    with contextlib.closing(progress):
        result_local_image = await root.client.images.pull(
            remote_obj, local_obj, progress=progress
        )
    click.echo(result_local_image)


@command()
@async_cmd()
async def ls(root: Root) -> None:
    """
    List images.
    """

    images = await root.client.images.ls()
    for image in images:
        click.echo(image)


@command()
@click.argument("image", type=RemoteTaglessImageType())
@async_cmd()
async def tags(root: Root, image: RemoteImage) -> None:
    """
    List tags for image in platform registry.

    Image name must be URL with image:// scheme.

    Examples:

    neuro image tags image://myfriend/alpine
    neuro image tags image:myimage
    """

    tags = await root.client.images.tags(image)
    for tag in tags:
        click.echo(tag)


image.add_command(ls)
image.add_command(push)
image.add_command(pull)
image.add_command(tags)
