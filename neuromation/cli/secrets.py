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

    ret = []
    async for secret in root.client.secrets.list():
        ret.append(secret.key)
        pager_maybe(ret, root.tty, root.terminal_size)


@command()
@argument("key")
@argument("value")
async def add(root: Root, key: str, value: str) -> None:
    """
    Add secret.
    """

    await root.client.secrets.add(key, value.encode("utf-8"))


@command()
@argument("key")
async def rm(root: Root, key: str) -> None:
    """
    Add secret.
    """

    await root.client.secrets.rm(key)


secret.add_command(ls)
secret.add_command(add)
secret.add_command(rm)
