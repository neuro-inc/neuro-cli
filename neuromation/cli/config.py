import json
import os
from pathlib import Path
from typing import Any, Dict

import click
from yarl import URL

from neuromation.api import login as api_login, logout as api_logout

from .defaults import API_URL
from .formatters import ConfigFormatter
from .root import Root
from .utils import async_cmd, command, group


@group()
def config() -> None:
    """Client configuration."""


@command()
@click.pass_obj
def show(root: Root) -> None:
    """
    Print current settings.
    """
    fmt = ConfigFormatter()
    click.echo(fmt(root))


@command()
@click.pass_obj
def show_token(root: Root) -> None:
    """
    Print current authorization token.
    """
    click.echo(root.auth)


@command()
@click.argument("url", required=False, default=API_URL, type=URL)
@async_cmd(read_config=False)
async def login(root: Root, url: URL) -> None:
    """
    Log into Neuromation Platform.
    """
    await api_login(url, path=root.config_path, timeout=root.timeout)
    click.echo(f"Logged into {url}")


@command()
@async_cmd()
async def logout(root: Root) -> None:
    """
    Log out.
    """
    await api_logout(path=root.config_path)
    click.echo("Logged out")


@command(name="docker")
@click.option(
    "--docker-config",
    metavar="PATH",
    type=click.Path(file_okay=False),
    help="Specifies the location of the Docker client configuration files",
    default=lambda: os.environ.get("DOCKER_CONFIG", Path.home() / ".docker"),
    show_default=False,
)
@async_cmd()
async def docker(root: Root, docker_config: str) -> None:
    """
    Configure docker client for working with platform registry
    """
    config_path = Path(docker_config)
    if not config_path.exists():
        config_path.mkdir(parents=True)
    elif not config_path.is_dir():
        raise ValueError(f"Specified path is not a directory: {config}")

    json_path = config_path / "config.json"
    payload: Dict[str, Any] = {}
    if json_path.exists():
        with json_path.open("r") as file:
            payload = json.load(file)
    if "credHelpers" not in payload:
        payload["credHelpers"] = {}

    registry = URL(root.registry_url).host
    payload["credHelpers"][registry] = "neuro"
    with json_path.open("w") as file:
        json.dump(payload, file, indent=2)


config.add_command(login)
config.add_command(show)
config.add_command(show_token)

config.add_command(docker)

config.add_command(logout)
