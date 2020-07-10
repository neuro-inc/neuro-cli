import os
import sys
from pathlib import Path

import click

from .root import Root
from .utils import argument, group


CFG_FILE = {"bash": Path("~/.bashrc"), "zsh": Path("~/.zshrc")}
SOURCE_CMD = {"bash": "source", "zsh": "source_zsh"}

ACTIVATION_TEMPLATE = 'eval "$(_NEURO_COMPLETE={cmd} {exe})"'


@group()
def completion() -> None:
    """
    Output shell completion code.
    """


@completion.command()
@argument("shell", type=click.Choice(["bash", "zsh"]))
async def generate(root: Root, shell: str) -> None:
    """
    Provide an instruction for shell completion generation.
    """
    click.echo(f"Push the following line into your {CFG_FILE[shell]}")
    click.echo(ACTIVATION_TEMPLATE.format(cmd=SOURCE_CMD[shell], exe=sys.argv[0]))


@completion.command()
@argument("shell", type=click.Choice(["bash", "zsh"]))
async def patch(root: Root, shell: str) -> None:
    """
    Automatically patch shell configuration profile to enable completion
    """
    profile_file = CFG_FILE[shell].expanduser()
    with profile_file.open("ab+") as profile:
        profile.write(
            b"\n"
            + os.fsencode(
                ACTIVATION_TEMPLATE.format(cmd=SOURCE_CMD[shell], exe=sys.argv[0])
            )
            + b"\n"
        )
