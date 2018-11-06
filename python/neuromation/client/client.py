import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

from aiohttp.client import ClientTimeout

from neuromation.http import fetch, session
from neuromation.http.fetch import (
    AccessDeniedError as FetchAccessDeniedError,
    BadRequestError,
    FetchError,
    MethodNotAllowedError,
    NotFoundError,
    UnauthorizedError,
)

from .requests import Request, build


log = logging.getLogger(__name__)


class ClientError(Exception):
    pass


class IllegalArgumentError(ValueError):
    pass


class AuthError(ClientError):
    pass


class AuthenticationError(AuthError):
    pass


class AuthorizationError(AuthError):
    pass


class ResourceNotFound(ValueError):
    pass


@dataclass(frozen=True)
class TimeoutSettings:
    total: Optional[float]
    connect: Optional[float]
    sock_read: Optional[float]
    sock_connect: Optional[float]


# AIO HTTP Default Timeout Settings
DEFAULT_CLIENT_TIMEOUT_SETTINGS = TimeoutSettings(None, None, 30, 30)


class ApiClient:
    def __init__(
        self,
        url: str,
        token: str,
        timeout: Optional[TimeoutSettings] = DEFAULT_CLIENT_TIMEOUT_SETTINGS,
        *,
        loop: Optional[asyncio.events.AbstractEventLoop] = None,
    ) -> None:
        self._url = url
        self._loop = loop if loop else asyncio.get_event_loop()
        self._exception_map = {
            FetchAccessDeniedError: AuthorizationError,
            UnauthorizedError: AuthenticationError,
            BadRequestError: IllegalArgumentError,
            NotFoundError: ResourceNotFound,
            MethodNotAllowedError: ClientError,
        }
        client_timeout = None
        if timeout:
            client_timeout = ClientTimeout(  # type: ignore
                total=timeout.total,
                connect=timeout.connect,
                sock_connect=timeout.sock_connect,
                sock_read=timeout.sock_read,
            )
        self._session_object = session(token=token, timeout=client_timeout)
        self._session = self.loop.run_until_complete(self._session_object)

    def __enter__(self) -> "ApiClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.loop.run_until_complete(self.close())

    @property
    def loop(self) -> asyncio.events.AbstractEventLoop:
        return self._loop

    async def close(self) -> None:
        if self._session and self._session.closed:
            return

        await self._session.close()
        self._session = None

    async def _fetch(self, request: Request) -> Any:
        try:
            return await fetch(build(request), session=self._session, url=self._url)
        except FetchError as error:
            error_class = type(error)
            log.debug(f"Error {error_class} {error}")
            mapped_class = self._exception_map.get(error_class, error_class)
            raise mapped_class(error) from error

    def _fetch_sync(self, request: Request) -> Any:
        res = self._loop.run_until_complete(self._fetch(request))
        log.debug(res)
        return res
