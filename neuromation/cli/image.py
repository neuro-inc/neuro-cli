import contextlib
import logging
from typing import Optional

import click
from rich import box
from rich.progress import Progress
from rich.table import Table

from neuromation.api import LocalImage, RemoteImage
from neuromation.cli.formatters.images import (
    BaseImagesFormatter,
    DockerImageProgress,
    LongImagesFormatter,
    QuietImagesFormatter,
    ShortImagesFormatter,
)
from neuromation.cli.formatters.utils import (
    ImageFormatter,
    image_formatter,
    uri_formatter,
)

from .click_types import RemoteImageType, RemoteTaglessImageType
from .root import Root
from .utils import (
    argument,
    command,
    deprecated_quiet_option,
    format_size,
    group,
    option,
)


log = logging.getLogger(__name__)


@group()
def image() -> None:
    """
    Container image operations.
    """


@command()
@argument("local_image")
@argument("remote_image", required=False)
@deprecated_quiet_option
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

    progress = DockerImageProgress.create(console=root.console, quiet=root.quiet)
    local_obj = root.client.parse.local_image(local_image)
    if remote_image is not None:
        remote_obj: Optional[RemoteImage] = root.client.parse.remote_image(remote_image)
    else:
        remote_obj = None
    with contextlib.closing(progress):
        result_remote_image = await root.client.images.push(
            local_obj, remote_obj, progress=progress
        )
    root.print(result_remote_image)


@command()
@argument("remote_image")
@argument("local_image", required=False)
@deprecated_quiet_option
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

    progress = DockerImageProgress.create(console=root.console, quiet=root.quiet)
    remote_obj = root.client.parse.remote_image(remote_image)
    if local_image is not None:
        local_obj: Optional[LocalImage] = root.client.parse.local_image(local_image)
    else:
        local_obj = None
    with contextlib.closing(progress):
        result_local_image = await root.client.images.pull(
            remote_obj, local_obj, progress=progress
        )
    root.print(result_local_image)


@command()
@option("-l", "format_long", is_flag=True, help="List in long format.")
@option("--full-uri", is_flag=True, help="Output full image URI.")
async def ls(root: Root, format_long: bool, full_uri: bool) -> None:
    """
    List images.
    """

    images = await root.client.images.ls()

    image_fmtr: ImageFormatter
    if full_uri:
        image_fmtr = str
    else:
        uri_fmtr = uri_formatter(
            username=root.client.username, cluster_name=root.client.cluster_name
        )
        image_fmtr = image_formatter(uri_formatter=uri_fmtr)
    formatter: BaseImagesFormatter
    if root.quiet:
        formatter = QuietImagesFormatter(image_formatter=image_fmtr)
    elif format_long:
        formatter = LongImagesFormatter(image_formatter=image_fmtr)
    else:
        formatter = ShortImagesFormatter(image_formatter=image_fmtr)
    with root.pager():
        root.print(formatter(images))


@command()
@option("-s", "print_size", is_flag=True, help="Print tag sizes.")
@argument("image", type=RemoteTaglessImageType())
async def tags(root: Root, print_size: bool, image: RemoteImage) -> None:
    """
    List tags for image in platform registry.

    Image name must be URL with image:// scheme.

    Examples:

    neuro image tags image://myfriend/alpine
    neuro image tags image:myimage
    """

    images = await root.client.images.tags(image)
    table = Table(box=box.SIMPLE_HEAVY)
    table.add_column("Tag", style="bold")
    if print_size:
        table.add_column("Size")
    with root.pager():
        with Progress() as progress:
            if print_size:
                task = progress.add_task("Getting image sizes...", total=len(images))
            for image in images:
                if print_size:
                    table.add_row(
                        str(image), format_size(await root.client.images.size(image))
                    )
                    progress.update(task, advance=1)
                else:
                    table.add_row(str(image))
        root.print(table)


@command()
@argument("image", type=RemoteImageType())
async def rm(root: Root, image: RemoteImage) -> None:
    """
    Remove image from platform registry.

    Image name must be URL with image:// scheme.
    Image name must contain tag.

    Examples:

    neuro image rm image://myfriend/alpine:shared
    neuro image rm image:myimage:latest
    """
    digest = await root.client.images.digest(image)
    click.echo(f"Deleting image identified by {digest}")
    await root.client.images.rm(image, digest)


@command()
@argument("image", type=RemoteImageType())
async def size(root: Root, image: RemoteImage) -> None:
    """
    Get image size

    Image name must be URL with image:// scheme.
    Image name must contain tag.

    Examples:

    neuro image size image://myfriend/alpine:shared
    neuro image size image:myimage:latest
    """
    size = await root.client.images.size(image)
    click.echo(format_size(size))


@command()
@argument("image", type=RemoteImageType())
async def digest(root: Root, image: RemoteImage) -> None:
    """
    Get digest of an image from remote registry

    Image name must be URL with image:// scheme.
    Image name must contain tag.

    Examples:

    neuro image digest image://myfriend/alpine:shared
    neuro image digest image:myimage:latest
    """
    res = await root.client.images.digest(image)
    root.print(res)


image.add_command(ls)
image.add_command(push)
image.add_command(pull)
image.add_command(rm)
image.add_command(size)
image.add_command(digest)
image.add_command(tags)
