from pathlib import Path

import click

from .utils import group


CFG_FILE = {"bash": Path("~/.bashrc"), "zsh": Path("~/.zshrc")}
SOURCE_CMD = {"bash": "source", "zsh": "source_zsh"}

ACTIVATION_TEMPLATE = 'eval "$(_NEURO_COMPLETE={cmd} neuro)"'


@group()
def completion() -> None:
    """
    Output shell completion code.
    """


@completion.command()
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh"]),
    help="Shell type.",
    default="bash",
    show_default=True,
)
def generate(shell: str) -> None:
    """
    Provide an instruction for shell completion generation.
    """
    click.echo(f"Push the following line into your {CFG_FILE[shell]}")
    click.echo(ACTIVATION_TEMPLATE.format(cmd=SOURCE_CMD[shell]))


@completion.command()
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh"]),
    help="Shell type.",
    default="bash",
    show_default=True,
)
def patch(shell: str) -> None:
    """
    Automatically patch shell configuration profile to enable completion
    """
    profile_file = CFG_FILE[shell].expanduser()
    with profile_file.open("a+") as profile:
        profile.write(ACTIVATION_TEMPLATE.format(cmd=SOURCE_CMD[shell]))
        profile.write("\n")
