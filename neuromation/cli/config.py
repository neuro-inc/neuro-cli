import asyncio
import json
import os
import sys
import webbrowser
from pathlib import Path
from typing import Any, Dict

import click
from yarl import URL

from neuromation.api import (
    DEFAULT_API_URL,
    ConfigError,
    login as api_login,
    login_headless as api_login_headless,
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

    async def show_browser(url: URL) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, webbrowser.open_new, str(url))

    try:
        await api_login(
            show_browser, url=url, path=root.config_path, timeout=root.timeout
        )
    except ConfigError:
        await api_logout(path=root.config_path)
        click.echo("You were successfully logged out.")
        await api_login(
            show_browser, url=url, path=root.config_path, timeout=root.timeout
        )
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
@click.argument("url", required=False, default=DEFAULT_API_URL, type=URL)
@async_cmd(init_client=False)
async def login_headless(root: Root, url: URL) -> None:
    """
    Log into Neuromation Platform from non-GUI server environment.

    URL is a platform entrypoint URL.

    The command works similar to "neuro login" but instead of
    opening a browser for performing OAuth registration prints
    an URL that should be open on guest host.

    Then user inputs a code displayed in a browser after successful login
    back in neuro command to finish the login process.
    """

    async def login_callback(url: URL) -> str:
        click.echo(f"Open {url} in a browser")
        click.echo("Put the code displayed in a browser after successful login")
        auth_code = input("Code (empty for exit)-> ")
        if not auth_code:
            sys.exit()
        return auth_code

    try:
        await api_login_headless(
            login_callback, url=url, path=root.config_path, timeout=root.timeout
        )
    except ConfigError:
        await api_logout(path=root.config_path)
        click.echo("You were successfully logged out.")
        await api_login_headless(
            login_callback, url=url, path=root.config_path, timeout=root.timeout
        )
    click.echo(f"Logged into {url}")


@command()
@async_cmd(init_client=False)
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

    json_path_str = f"{json_path}"
    registry_str = click.style(f"{registry}", bold=True)
    click.echo(f"Configuration file {json_path_str} updated.")
    click.echo(f"You can use docker client with neuro registry: {registry_str}")


config.add_command(login)
config.add_command(login_with_token)
config.add_command(login_headless)
config.add_command(show)
config.add_command(show_token)

config.add_command(docker)

config.add_command(logout)
