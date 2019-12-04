import errno
import json as jsonmodule
import logging
from http.cookies import Morsel  # noqa
from types import SimpleNamespace
from typing import Any, AsyncIterator, Dict, Mapping, Optional

import aiohttp
from aiohttp import WSMessage
from multidict import CIMultiDict
from yarl import URL

from .tracing import gen_trace_id
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
        cookie: Optional["Morsel[str]"],
        trace_id: Optional[str],
    ) -> None:
        self._session = session
        self._trace_id = trace_id
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

    @asynccontextmanager
    async def request(
        self,
        method: str,
        url: URL,
        *,
        auth: str,
        params: Optional[Mapping[str, str]] = None,
        data: Any = None,
        json: Any = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[aiohttp.ClientTimeout] = None,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        assert url.is_absolute()
        log.debug("Fetch [%s] %s", method, url)
        if headers is not None:
            real_headers: CIMultiDict[str] = CIMultiDict(headers)
        else:
            real_headers = CIMultiDict()
        real_headers["Authorization"] = auth
        trace_request_ctx = SimpleNamespace()
        trace_id = self._trace_id
        if trace_id is None:
            trace_id = gen_trace_id()
        trace_request_ctx.trace_id = trace_id
        async with self._session.request(
            method,
            url,
            headers=real_headers,
            params=params,
            json=json,
            data=data,
            timeout=timeout,
            trace_request_ctx=trace_request_ctx,
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
        self, abs_url: URL, auth: str, *, headers: Optional[Dict[str, str]] = None
    ) -> AsyncIterator[WSMessage]:
        # TODO: timeout
        assert abs_url.is_absolute(), abs_url
        log.debug("Fetch web socket: %s", abs_url)

        if headers is not None:
            real_headers: CIMultiDict[str] = CIMultiDict(headers)
        else:
            real_headers = CIMultiDict()
        real_headers["Authorization"] = auth

        async with self._session.ws_connect(abs_url, headers=real_headers) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    yield msg
