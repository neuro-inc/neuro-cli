import asyncio
import logging
import sys
from functools import partial
from pathlib import Path
from types import TracebackType
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Generator,
    Generic,
    Iterator,
    Optional,
    Tuple,
    Type,
    TypeVar,
)

import aiohttp

from .errors import ConfigError

_T = TypeVar("_T")


if sys.version_info >= (3, 7):
    from typing import AsyncContextManager
else:

    class AsyncContextManager(Generic[_T]):
        async def __aenter__(self) -> _T:
            pass  # pragma: no cover

        async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc: Optional[BaseException],
            tb: Optional[TracebackType],
        ) -> Optional[bool]:
            pass  # pragma: no cover


class NoPublicConstructor(type):
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        raise TypeError("no public constructor")

    def _create(self, *args: Any, **kwargs: Any) -> Any:

        return super().__call__(*args, **kwargs)


class _ContextManager(Generic[_T], Awaitable[_T], AsyncContextManager[_T]):

    __slots__ = ("_coro", "_ret")

    def __init__(self, coro: Coroutine[Any, Any, _T]) -> None:
        self._coro = coro
        self._ret: Optional[_T] = None

    def __await__(self) -> Generator[Any, None, _T]:
        return self._coro.__await__()

    async def __aenter__(self) -> _T:
        self._ret = await self._coro
        assert self._ret is not None
        return self._ret

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> Optional[bool]:
        assert self._ret is not None
        # ret supports async close() protocol
        # Need to teach mypy about this facility
        await self._ret.close()  # type: ignore
        return None


log = logging.getLogger(__name__)


class retries:
    def __init__(
        self, msg: str, attempts: int = 10, logger: Callable[[str], None] = log.info
    ) -> None:
        self._msg = msg
        self._attempts = attempts
        self._logger = logger
        self.reset()

    def reset(self) -> None:
        self._attempt = 0
        self._sleeptime = 0.0

    def __iter__(self) -> Iterator["retries"]:
        while self._attempt < self._attempts:
            self._sleeptime += 0.1
            self._attempt += 1
            yield self

    async def __aenter__(self) -> None:
        pass

    async def __aexit__(
        self, type: Type[BaseException], value: BaseException, tb: Any
    ) -> bool:
        if type is None:
            # Stop iteration
            self._attempt = self._attempts
        elif issubclass(type, aiohttp.ClientError) and self._attempt < self._attempts:
            self._logger(f"{self._msg}: {value}.  Retry...")
            await asyncio.sleep(self._sleeptime)
            return True
        return False


def flat(sql: str) -> str:
    return " ".join(line.strip() for line in sql.splitlines() if line.strip())


def find_project_root(path: Optional[Path] = None) -> Path:
    if path is None:
        path = Path.cwd()
    here = path
    while here.parent != here:
        config = here / ".neuro.toml"
        if config.exists():
            return here
        here = here.parent
    raise ConfigError(f"Project root is not found for {path}")


QueuedCall = Callable[[], Any]


async def _noop(*args: Any, **kwargs: Any) -> None:
    pass


class _NoopProxy:
    def __getattr__(self, name: str) -> Callable[[Any], Coroutine[Any, Any, None]]:
        return _noop


def queue_calls(
    any_obj: Any,
    allow_any_for_none: bool = True,
) -> Tuple["asyncio.Queue[QueuedCall]", Any]:  # Sadly, but there is now way to annotate
    """Add calls to asyncio.Queue instead executing them directly

    Wraps given object into proxy, so trying to call any of its method will produce
    a coroutine, that add QueuedCall to queue. For example, the following code:

    class Foo:
        def bar(self, arg):
            print(arg)
    queue, wrapped = queue_calls(Foo())
    await wrapped.bar("foo")

    Will add partial(foo.bar, "foo",)) to the queue and will not print
    anything.

    To execute calls, you can do next:

    queued_call = await queue.get()
    queued_call.execute()

    In case `any_obj` is `None` and `allow_any_for_none` is set, then a proxy will not
    raise any AttributeErrors and just absorb all cals silently.
    """
    queue: "asyncio.Queue[QueuedCall]" = asyncio.Queue()

    async def add_to_queue(
        real_method: Callable[..., None], *args: Any, **kwargs: Any
    ) -> None:
        await queue.put(partial(real_method, *args, **kwargs))

    class Proxy:
        def __getattr__(self, name: str) -> Callable[[Any], Coroutine[Any, Any, None]]:
            real_method = getattr(any_obj, name)
            setattr(self, name, partial(add_to_queue, real_method))
            return partial(add_to_queue, real_method)

    if any_obj is None and allow_any_for_none:
        return queue, _NoopProxy()

    return queue, Proxy()
