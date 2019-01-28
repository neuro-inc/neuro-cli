import sys

import click
from yarl import URL

# TODO(asvetlov): rename the class to avoid the namig conflict
from neuromation.client.images import Image

from .command_spinner import SpinnerBase
from .utils import Context, run_async


@click.group()
def image() -> None:
    """
    Docker image operations
    """


@image.command()
@click.argument("image_name")
@click.argument("remote_image_name", required=False)
@click.pass_obj
@run_async
async def push(ctx: Context, image_name: str, remote_image_name: str) -> None:
    """
    Push an image to platform registry.

    Remote image must be URL with image:// scheme.
    Image names can contains tag. If tags not specified 'latest' will
    be used as value.

    Examples:

    \b
        neuro image push myimage
        neuro image push alpine:latest image:my-alpine:production
        neuro image push alpine image://myfriend/alpine:shared

    """

    username = ctx.username

    local_image = remote_image = Image.from_local(image_name, username)
    if remote_image_name:
        remote_image = Image.from_url(URL(remote_image_name), username)

    spinner = SpinnerBase.create_spinner(sys.stdout.isatty(), "Pushing image {}  ")

    async with ctx.make_client() as client:
        result_remote_image = await client.images.push(
            local_image, remote_image, spinner
        )
        click.echo(result_remote_image.url)


@image.command()
@click.argument("image_name")
@click.argument("local_image_name", required=False)
@click.pass_obj
@run_async
async def pull(ctx: Context, image_name: str, local_image_name: str) -> None:
    """
    Pull an image from platform registry.

    Remote image name must be URL with image:// scheme.
    Image names can contain tag.

    Examples:

    \b
        neuro image pull image:myimage
        neuro image pull image://myfriend/alpine:shared
        neuro image pull image://username/my-alpine:production alpine:from-registry

    """

    username = ctx.username

    remote_image = local_image = Image.from_url(URL(image_name), username)
    if local_image_name:
        local_image = Image.from_local(local_image_name, username)

    spinner = SpinnerBase.create_spinner(sys.stdout.isatty(), "Pulling image {}  ")

    async with ctx.make_client() as client:
        result_local_image = await client.images.pull(
            remote_image, local_image, spinner
        )
        click.echo(result_local_image.local)


@image.command()
@click.pass_obj
@run_async
async def ls(ctx: Context) -> None:
    """
    List user's images which are available for jobs.

    You will see here own and shared with you images
    """

    async with ctx.make_client() as client:
        images = await client.images.ls()
        for image in images:
            click.echo(image)
