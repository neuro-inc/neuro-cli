import errno
import json as jsonmodule
import logging
from http.cookies import Morsel  # noqa
from typing import Any, AsyncIterator, Dict, Mapping, Optional

import aiohttp
from aiohttp import WSMessage
from multidict import CIMultiDict
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


class ServerNotAvailable(ValueError):
    pass


class _Core:
    """Transport provider for public API client.

    Internal class.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: URL,
        token: str,
        cookie: Optional["Morsel[str]"],
    ) -> None:
        self._session = session
        self._base_url = base_url
        self._token = token
        self._headers = self._auth_headers()
        if cookie is not None:
            self._session.cookie_jar.update_cookies(
                {"NEURO_SESSION": cookie}  # type: ignore
                # TODO: pass cookie["domain"]
            )
        self._exception_map = {
            400: IllegalArgumentError,
            401: AuthenticationError,
            403: AuthorizationError,
            404: ResourceNotFound,
            405: ClientError,
            502: ServerNotAvailable,
        }

    @property
    def timeout(self) -> aiohttp.ClientTimeout:
        # TODO: implement ClientSession.timeout public property for session
        return self._session._timeout

    @property
    def session(self) -> aiohttp.ClientSession:
        return self._session

    async def close(self) -> None:
        pass

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
        if headers is not None:
            real_headers = CIMultiDict(headers)
        else:
            real_headers = CIMultiDict()
        real_headers.update(self._headers)
        async with self._session.request(
            method,
            url,
            headers=real_headers,
            params=params,
            json=json,
            data=data,
            timeout=timeout,
        ) as resp:
            if 400 <= resp.status:
                err_text = await resp.text()
                if resp.content_type.lower() == "application/json":
                    payload = jsonmodule.loads(err_text)
                    if "error" in payload:
                        err_text = payload["error"]
                else:
                    payload = {}
                if resp.status == 400 and "errno" in payload:
                    os_errno: Any = payload["errno"]
                    os_errno = errno.__dict__.get(os_errno, os_errno)
                    raise OSError(os_errno, err_text)
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

        if headers is not None:
            real_headers = CIMultiDict(headers)
        else:
            real_headers = CIMultiDict()
        real_headers.update(self._headers)

        async with self._session.ws_connect(abs_url, headers=real_headers) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    yield msg
