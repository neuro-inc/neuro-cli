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
@click.option(
    "--no-input",
    is_flag=True,
    required=False,
    default=False,
    help="Don't ask any questions, use default values for project setup",
    hidden=True,
)
async def init(root: Root, slug: str, no_input: bool) -> None:
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
        f"gh:neuromation/cookiecutter-neuro-project",
        extra_context=extra_context,
        no_input=no_input,
    )


project.add_command(init)
