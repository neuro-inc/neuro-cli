import pathlib

import click

from .formatters.ftable import table
from .root import Root
from .utils import argument, command, group, pager_maybe


@group()
def secret() -> None:
    """
    Operations with secrets.
    """


@command()
async def ls(root: Root) -> None:
    """
    List secrets.
    """

    ret = [[click.style("Key", bold=True)]]
    async for secret in root.client.secrets.list():
        ret.append([secret.key])
    pager_maybe(table(ret), root.tty, root.terminal_size)


@command()
@argument("key")
@argument("value")
async def add(root: Root, key: str, value: str) -> None:
    """
    Add secret KEY with data VALUE.

    If VALUE starts with @ it points to a file with secrets content.

    Examples:

      neuro secret add KEY_NAME VALUE
      neuro secret add KEY_NAME @path/to/file.txt
    """
    await root.client.secrets.add(key, read_data(value))


@command()
@argument("key")
async def rm(root: Root, key: str) -> None:
    """
    Add secret KEY.
    """

    await root.client.secrets.rm(key)


secret.add_command(ls)
secret.add_command(add)
secret.add_command(rm)


def read_data(value: str) -> bytes:
    if value.startswith("@"):
        # Read from file
        data = pathlib.Path(value[1:]).expanduser().read_bytes()
    else:
        data = value.encode("utf-8")
    return data
