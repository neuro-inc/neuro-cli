import asyncio
import logging
import sys
from types import TracebackType
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Coroutine,
    Generator,
    Generic,
    Iterator,
    Optional,
    Type,
    TypeVar,
)

import aiohttp


if sys.version_info >= (3, 7):  # pragma: no cover
    from contextlib import asynccontextmanager  # noqa
else:
    from async_generator import asynccontextmanager  # noqa

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


def retries(
    msg: str, attempts: int = 10, logger: Callable[[str], None] = log.info
) -> Iterator[AsyncContextManager[None]]:
    sleeptime = 0.0
    while attempts:

        @asynccontextmanager
        async def retry() -> AsyncIterator[None]:
            nonlocal attempts
            if attempts:
                try:
                    yield
                except aiohttp.ClientError as err:
                    logger(f"{msg}: {err}.  Retry...")
                    await asyncio.sleep(sleeptime)
                else:
                    attempts = 0
            else:
                yield

        sleeptime += 0.1
        attempts -= 1
        yield retry()


def flat(sql: str) -> str:
    return " ".join(line.strip() for line in sql.splitlines() if line.strip())
