import click

from . import rc


@click.group()
def config() -> None:
    """Client configuration settings commands."""


@config.command()
@click.argument("url")
def url(url: str) -> None:
    """
    Updates settings with provided platform URL.

    Examples:

    \b
        neuro config url https://platform.neuromation.io/api/v1
    """
    rc.ConfigFactory.update_api_url(url)


@config.command(name="id_rsa")
@click.argument("file", type=click.Path(exists=True, readable=True, dir_okay=False))
def id_rsa(file: str) -> None:
    """
    Updates path to id_rsa file with private key.

    FILE is being used for accessing remote shell, remote debug.

    Note: this is temporal and going to be
    replaced in future by JWT token.
    """
    rc.ConfigFactory.update_github_rsa_path(file)


@config.command()
def show() -> None:
    """
    Prints current settings.
    """
    config = rc.ConfigFactory.load()
    click.echo(config)


@config.command()
@click.option(
    "--insecure",
    is_flag=True,
    help="Store token in plain file instead system secured keyring",
)
@click.argument("token")
def auth(token: str, insecure: bool) -> None:
    """
    Updates authorization token.
    """
    # TODO (R Zubairov, 09/13/2018): check token correct
    # connectivity, check with Alex
    # Do not overwrite token in case new one does not work
    # TODO (R Zubairov, 09/13/2018): on server side we shall implement
    # protection against brute-force
    rc.ConfigFactory.update_auth_token(token=token, insecure=insecure)


@config.command()
def forget() -> None:
    """
    Forget authorization token.

    """
    rc.ConfigFactory.forget_auth_token()
