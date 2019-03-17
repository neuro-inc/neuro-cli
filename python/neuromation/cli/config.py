import json
from pathlib import Path
from typing import Any, Dict

import click
from yarl import URL

from . import rc
from .defaults import API_URL
from .formatters import ConfigFormatter
from .rc import Config
from .utils import async_cmd, command, group


@group()
def config() -> None:
    """Client configuration."""


@command(hidden=True)
@click.argument("url")
@async_cmd
async def url(cfg: Config, url: str) -> None:
    """
    Update settings with provided platform URL.

    Examples:

    neuro config url https://platform.neuromation.io/api/v1
    """
    await rc.ConfigFactory.update_api_url(url)


@command(hidden=True, name="id_rsa")
@click.argument("file", type=click.Path(exists=True, readable=True, dir_okay=False))
def id_rsa(file: str) -> None:
    """
    Update path to id_rsa file with private key.

    FILE is being used for accessing remote shell, remote debug.

    Note: this is temporal and going to be
    replaced in future by JWT token.
    """
    rc.ConfigFactory.update_github_rsa_path(file)


@command()
@click.pass_obj
def show(cfg: Config) -> None:
    """
    Print current settings.
    """
    fmt = ConfigFormatter()
    click.echo(fmt(cfg))


@command()
@click.pass_obj
def show_token(cfg: Config) -> None:
    """
    Print current authorization token.
    """
    click.echo(cfg.auth)


@command()
@click.argument("token")
def auth(token: str) -> None:
    """
    Update authorization token.
    """
    # TODO (R Zubairov, 09/13/2018): check token correct
    # connectivity, check with Alex
    # Do not overwrite token in case new one does not work
    # TODO (R Zubairov, 09/13/2018): on server side we shall implement
    # protection against brute-force
    rc.ConfigFactory.update_auth_token(token=token)


@command(hidden=True, deprecated=True)
def forget() -> None:
    """
    Forget authorization token.
    """
    rc.ConfigFactory.forget_auth_token()


@command()
@click.argument("url", required=False, default=API_URL, type=URL)
@async_cmd
async def login(cfg: Config, url: URL) -> None:
    """
    Log into Neuromation Platform.
    """
    await rc.ConfigFactory.refresh_auth_token(url)
    click.echo(f"Logged into {url}")


@command()
def logout() -> None:
    """
    Log out.
    """
    rc.ConfigFactory.forget_auth_token()
    click.echo("Logged out")


@command()
@click.option(
    "--config",
    metavar="PATH",
    type=str,
    help="Specifies the location of the Docker client configuration files",
    default=Path.home() / ".docker",
    show_default=False,
)
@click.pass_obj
def docker(cfg: Config, config: str) -> None:
    """
    Configure docker client for working with platform registry
    """
    config_path = Path(config)
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

    registry = URL(cfg.registry_url).host
    payload["credHelpers"][registry] = "neuro"
    with json_path.open("w") as file:
        json.dump(payload, file, indent=2)


config.add_command(login)
config.add_command(show)
config.add_command(show_token)

config.add_command(docker)

config.add_command(auth)
config.add_command(logout)

config.add_command(url)
config.add_command(id_rsa)
config.add_command(forget)
