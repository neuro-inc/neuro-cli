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

    # Initializes a scaffolding for the new project with the recommended
    # project structure:
    #   .
    #   ├── {project_name}     # directory with your code
    #   ├── data               # directory with your dataset
    #   ├── notebooks          # directory with your jupyter notebooks
    #   ├── Makefile           # directory with your datasets
    #   ├── apt.txt            # system-wide requirements (apt-get install ...)
    #   ├── requirements.txt   # Python requirements (pip install ...)
    #   ├── setup.py           # project configuration script
    #   └── setup.cfg          # project configuration file
    neuro project init my-wunderbar-project
    """
    cookiecutter("gh:neuromation/cookiecutter-neuro-project")


project.add_command(init)
