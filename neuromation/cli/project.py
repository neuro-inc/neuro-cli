import logging

import click
from cookiecutter.main import cookiecutter

from .root import Root
from .utils import async_cmd, command, group


log = logging.getLogger(__name__)


@group()
def project() -> None:
    """
    Project operations.
    """


@command()
@async_cmd()
@click.argument("slug", required=False)
async def init(root: Root, slug: str) -> None:
    """
    Initialize an empty project.

    Examples:

    # Initializes a scaffolding for the new project with the recommended project
    # structure (see http://github.com/neuromation/cookiecutter-neuro-project)
    neuro project init

    # Initializes a scaffolding for the new project with the recommended project
    # structure and sets default project folder name to "example"
    neuro project init example
    """
    extra_context = None
    if slug:
        extra_context = {"project_slug": slug}
    cookiecutter(
        f"gh:neuromation/cookiecutter-neuro-project", extra_context=extra_context
    )


project.add_command(init)
