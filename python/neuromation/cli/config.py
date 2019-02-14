import click
from yarl import URL

from . import rc
from .defaults import API_URL
from .formatter import ConfigFormatter
from .rc import Config
from .utils import command, group, run_async


@group()
def config() -> None:
    """Client configuration."""


@command(hidden=True)
@click.argument("url")
@run_async
async def url(url: str) -> None:
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
def login(url: URL) -> None:
    """
    Log into Neuromation Platform.
    """
    rc.ConfigFactory.refresh_auth_token(url)
    click.echo(f"Logged into {url}")


@command()
def logout() -> None:
    """
    Log out.
    """
    rc.ConfigFactory.forget_auth_token()
    click.echo("Logged out")


config.add_command(login)
config.add_command(show)
config.add_command(show_token)

config.add_command(auth)
config.add_command(logout)

config.add_command(url)
config.add_command(id_rsa)
config.add_command(forget)
