from pathlib import Path
from types import TracebackType
from typing import (
    Any,
    AsyncContextManager,
    Awaitable,
    Coroutine,
    Generator,
    Optional,
    Type,
)

from yarl import URL

from .abc import AbstractProgress, AbstractSpinner
from .client import Client
from .config_factory import Factory
from .core import (
    AuthenticationError,
    AuthError,
    AuthorizationError,
    ClientError,
    IllegalArgumentError,
    ResourceNotFound,
)
from .images import DockerImage
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
from .models import TrainResult
from .parsing_utils import ImageNameParser
from .storage import FileStatus, FileStatusType
from .users import Action, Permission


__all__ = (
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
    "TrainResult",
    "Action",
    "Permission",
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
    "AbstractSpinner",
    "ImageNameParser",
    "DockerImage",
    "Factory",
    "get",
    "login",
    "login_with_token",
    "logout",
)


class _ContextManager(Awaitable[Client], AsyncContextManager[Client]):

    __slots__ = ("_func", "_client")

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


def get(*, path: Optional[Path] = None) -> _ContextManager:
    return _ContextManager(_get(path))


async def _get(path: Optional[Path]) -> Client:
    return await Factory(path).get()


def login(url: URL, *, path: Optional[Path] = None) -> _ContextManager:
    return _ContextManager(_login(url, path))


async def _login(url: URL, path: Optional[Path]) -> Client:
    return await Factory(path).login(url)


def login_with_token(
    url: URL, token: str, *, path: Optional[Path] = None
) -> _ContextManager:
    return _ContextManager(_login_with_token(url, token, path))


async def _login_with_token(url: URL, token: str, path: Optional[Path]) -> Client:
    return await Factory(path).login_with_token(url, token)


async def logout(*, path: Optional[Path] = None) -> None:
    return await Factory(path).logout()
