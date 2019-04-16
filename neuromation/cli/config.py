import json
import os
from pathlib import Path
from typing import Any, Dict

import click
from yarl import URL

from neuromation.api import (
    DEFAULT_API_URL,
    ConfigError,
    login as api_login,
    login_with_token as api_login_with_token,
    logout as api_logout,
)

from .formatters import ConfigFormatter
from .root import Root
from .utils import async_cmd, command, group


@group()
def config() -> None:
    """Client configuration."""


@command()
@async_cmd()
async def show(root: Root) -> None:
    """
    Print current settings.
    """
    fmt = ConfigFormatter()
    click.echo(fmt(root))


@command()
@async_cmd()
async def show_token(root: Root) -> None:
    """
    Print current authorization token.
    """
    click.echo(root.auth)


@command()
@click.argument("url", required=False, default=DEFAULT_API_URL, type=URL)
@async_cmd(init_client=False)
async def login(root: Root, url: URL) -> None:
    """
    Log into Neuromation Platform.

    URL is a platform entrypoint URL.
    """
    try:
        await api_login(url=url, path=root.config_path, timeout=root.timeout)
    except ConfigError:
        await api_logout(path=root.config_path)
        click.echo("You were successfully logged out.")
        await api_login(url=url, path=root.config_path, timeout=root.timeout)
    click.echo(f"Logged into {url}")


@command()
@click.argument("token", required=True, type=str)
@click.argument("url", required=False, default=DEFAULT_API_URL, type=URL)
@async_cmd(init_client=False)
async def login_with_token(root: Root, token: str, url: URL) -> None:
    """
    Log into Neuromation Platform with token.

    TOKEN is authentication token provided by Neuromation administration team.
    URL is a platform entrypoint URL.
    """
    try:
        await api_login_with_token(
            token, url=url, path=root.config_path, timeout=root.timeout
        )
    except ConfigError:
        await api_logout(path=root.config_path)
        click.echo("You were successfully logged out.")
        await api_login_with_token(
            token, url=url, path=root.config_path, timeout=root.timeout
        )
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
config.add_command(login_with_token)
config.add_command(show)
config.add_command(show_token)

config.add_command(docker)

config.add_command(logout)
