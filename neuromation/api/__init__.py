import sys
from pathlib import Path
from types import TracebackType
from typing import Any, Awaitable, Coroutine, Generator, Optional, Type

import aiohttp
from yarl import URL

from .abc import AbstractDockerImageProgress, AbstractProgress
from .client import Client
from .config_factory import (
    CONFIG_ENV_NAME,
    DEFAULT_API_URL,
    DEFAULT_CONFIG_PATH,
    ConfigError,
    Factory,
)
from .core import (
    DEFAULT_TIMEOUT,
    AuthenticationError,
    AuthError,
    AuthorizationError,
    ClientError,
    IllegalArgumentError,
    ResourceNotFound,
)
from .images import DockerImage, DockerImageOperation
from .jobs import (
    Container,
    HTTPPort,
    Image,
    JobDescription,
    JobStatus,
    JobStatusHistory,
    JobTelemetry,
    NetworkPortForwarding,
    Resources,
    Volume,
)
from .parsing_utils import ImageNameParser
from .storage import FileStatus, FileStatusType
from .users import Action, Permission, SharedPermission


if sys.version_info >= (3, 7):
    from typing import AsyncContextManager
else:
    from typing import Generic, TypeVar

    _T = TypeVar("_T")

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


__all__ = (
    "DEFAULT_API_URL",
    "DEFAULT_CONFIG_PATH",
    "CONFIG_ENV_NAME",
    "DockerImageOperation",
    "Image",
    "ImageNameParser",
    "JobDescription",
    "JobStatus",
    "JobStatusHistory",
    "JobTelemetry",
    "NetworkPortForwarding",
    "Resources",
    "Volume",
    "HTTPPort",
    "Action",
    "Permission",
    "SharedPermission",
    "Client",
    "FileStatusType",
    "FileStatus",
    "Container",
    "ResourceNotFound",
    "ClientError",
    "IllegalArgumentError",
    "AuthError",
    "AuthenticationError",
    "AuthorizationError",
    "AbstractProgress",
    "AbstractDockerImageProgress",
    "ImageNameParser",
    "DockerImage",
    "Factory",
    "get",
    "login",
    "login_with_token",
    "logout",
    "ConfigError",
)


class _ContextManager(Awaitable[Client], AsyncContextManager[Client]):

    __slots__ = ("_coro", "_client")

    def __init__(self, coro: Coroutine[Any, Any, Client]) -> None:
        self._coro = coro
        self._client: Optional[Client] = None

    def __await__(self) -> Generator[Any, None, Client]:
        return self._coro.__await__()

    async def __aenter__(self) -> Client:
        self._client = await self._coro
        assert self._client is not None
        return self._client

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> Optional[bool]:
        assert self._client is not None
        await self._client.close()
        return None


def get(
    *, path: Optional[Path] = None, timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT
) -> _ContextManager:
    return _ContextManager(_get(path, timeout))


async def _get(path: Optional[Path], timeout: aiohttp.ClientTimeout) -> Client:
    return await Factory(path).get(timeout=timeout)


async def login(
    *,
    url: URL = DEFAULT_API_URL,
    path: Optional[Path] = None,
    timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT
) -> None:
    await Factory(path).login(url=url, timeout=timeout)


async def login_with_token(
    token: str,
    *,
    url: URL = DEFAULT_API_URL,
    path: Optional[Path] = None,
    timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT
) -> None:
    await Factory(path).login_with_token(token, url=url, timeout=timeout)


async def logout(*, path: Optional[Path] = None) -> None:
    await Factory(path).logout()
