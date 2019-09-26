import logging

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
async def init(root: Root) -> None:
    """
    Initialize an empty project.

    Examples:

    # Initializes a scaffolding for the new project with the recommended project
    # structure (see http://github.com/neuromation/cookiecutter-neuro-project)
    neuro project init
    """
    cookiecutter(f"gh:neuromation/cookiecutter-neuro-project")


project.add_command(init)
