from dataclasses import dataclass
from functools import wraps
from typing import Any, Awaitable, Callable, Iterable, Optional, TypeVar

import aiohttp
import click
from yarl import URL

from neuromation.client import Client
from neuromation.client.users import get_token_username
from neuromation.utils import run

from . import rc


_T = TypeVar("_T")


@dataclass(frozen=True)
class Context:
    token: str
    url: URL

    @property
    def username(self) -> str:
        # This property intentionally fails for unregistered sessions etc.
        ret = get_token_username(self.token)
        assert ret
        return ret

    def make_client(self, *, timeout: Optional[aiohttp.ClientTimeout] = None) -> Client:
        kwargs = {}
        if timeout is not None:
            kwargs["timeout"] = timeout
        return Client(self.url, self.token, **kwargs)


def run_async(callback: Callable[..., Awaitable[_T]]) -> Callable[..., _T]:
    @wraps(callback)
    def wrapper(*args: Any, **kwargs: Any) -> _T:
        return run(callback(*args, **kwargs))

    return wrapper


def load_token() -> Optional[str]:
    config = rc.ConfigFactory.load()
    return config.auth


class DeprecatedGroup(click.MultiCommand):
    def __init__(
        self, origin: click.MultiCommand, name: Optional[str] = None, **attrs: Any
    ) -> None:
        attrs.setdefault("help", f"Alias for {origin.name}")
        attrs.setdefault("deprecated", True)
        super().__init__(name, **attrs)
        self.origin = origin

    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[click.Command]:
        return self.origin.get_command(ctx, cmd_name)

    def list_commands(self, ctx: click.Context) -> Iterable[str]:
        return self.origin.list_commands(ctx)
