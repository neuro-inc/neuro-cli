from functools import wraps
from typing import Any, Awaitable, Callable, Iterable, Optional, TypeVar

import click

from neuromation.utils import run


_T = TypeVar("_T")


def run_async(callback: Callable[..., Awaitable[_T]]) -> Callable[..., _T]:
    @wraps(callback)
    def wrapper(*args: Any, **kwargs: Any) -> _T:
        return run(callback(*args, **kwargs))

    return wrapper


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
