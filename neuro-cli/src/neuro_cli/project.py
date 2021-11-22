import logging
from typing import Optional

from cookiecutter.main import cookiecutter

from .root import Root
from .utils import argument, command, group

log = logging.getLogger(__name__)


@group(deprecated=True)
def project() -> None:
    """
    Project operations.
    """


@command(deprecated=True)
@argument("name", type=str, required=False)
async def init(root: Root, name: Optional[str]) -> None:
    """
    Initialize an empty project.

    Examples:

    # Initializes a scaffolding for the new project with the recommended project
    # structure (see http://github.com/neuro-inc/cookiecutter-neuro-project)
    neuro project init

    # Initializes a scaffolding for the new project with the recommended project
    # structure and sets the project name to 'my-project'
    neuro project init my-project
    """
    _project_init(name)


def _project_init(name: Optional[str], *, no_input: bool = False) -> None:
    extra_context = None
    if name:
        extra_context = {"project_name": name}
    cookiecutter(
        "gh:neuro-inc/cookiecutter-neuro-project",
        checkout="release",
        extra_context=extra_context,
        no_input=no_input,
    )


project.add_command(init)
