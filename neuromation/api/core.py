import logging
from http.cookies import Morsel  # noqa
from typing import Any, AsyncIterator, Dict, Mapping, Optional

import aiohttp
import attr
from aiohttp import WSMessage
from yarl import URL

from .utils import asynccontextmanager


log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(None, None, 60, 60)


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


class _Core:
    """Transport provider for public API client.

    Internal class.
    """

    def __init__(
        self,
        connector: aiohttp.BaseConnector,
        base_url: URL,
        token: str,
        cookie: Optional["Morsel[str]"],
        timeout: aiohttp.ClientTimeout,
    ) -> None:
        self._connector = connector
        self._base_url = base_url
        self._token = token
        self._timeout = timeout
        self._session = aiohttp.ClientSession(
            connector=connector,
            connector_owner=False,
            timeout=timeout,
            headers=self._auth_headers(),
        )
        if cookie is not None:
            self._session.cookie_jar.update_cookies(  # type: ignore
                {"NEURO_SESSION": cookie}
            )
        self._exception_map = {
            400: IllegalArgumentError,
            401: AuthenticationError,
            403: AuthorizationError,
            404: ResourceNotFound,
            405: ClientError,
        }

    @property
    def connector(self) -> aiohttp.BaseConnector:
        return self._connector

    @property
    def timeout(self) -> aiohttp.ClientTimeout:
        return self._timeout

    async def close(self) -> None:
        await self._session.close()

    def _auth_headers(self) -> Dict[str, str]:
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        return headers

    @asynccontextmanager
    async def request(
        self,
        method: str,
        url: URL,
        *,
        params: Optional[Mapping[str, str]] = None,
        data: Any = None,
        json: Any = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[aiohttp.ClientTimeout] = None,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        if not url.is_absolute():
            url = (self._base_url / "").join(url)
        log.debug("Fetch [%s] %s", method, url)
        if timeout is None:
            timeout = self._timeout
        if timeout.sock_read is not None:
            timeout = attr.evolve(timeout, total=3 * 60)
        async with self._session.request(
            method,
            url,
            headers=headers,
            params=params,
            json=json,
            data=data,
            timeout=timeout,
        ) as resp:
            if 400 <= resp.status:
                err_text = await resp.text()
                err_cls = self._exception_map.get(resp.status, IllegalArgumentError)
                raise err_cls(err_text)
            else:
                yield resp

    async def ws_connect(
        self, abs_url: URL, *, headers: Optional[Dict[str, str]] = None
    ) -> AsyncIterator[WSMessage]:
        # TODO: timeout
        assert abs_url.is_absolute(), abs_url
        log.debug("Fetch web socket: %s", abs_url)

        async with self._session.ws_connect(abs_url, headers=headers) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    yield msg
