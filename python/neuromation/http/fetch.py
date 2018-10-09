import asyncio
import logging
from contextlib import AbstractContextManager
from functools import singledispatch
from io import BufferedIOBase, BytesIO
from typing import Dict, Optional

import aiohttp
from async_generator import asynccontextmanager
from dataclasses import dataclass

log = logging.getLogger(__name__)


class FetchError(Exception):
    pass


class NotFoundError(FetchError):
    pass


class UnauthorizedError(FetchError):
    pass


class AccessDeniedError(FetchError):
    pass


class MethodNotAllowedError(FetchError):
    pass


class BadRequestError(FetchError):
    pass


@dataclass(frozen=True)
class Request:
    method: str
    # TODO(artyom, 07/04/2018): put a stricter type hint
    # that corresponds to URL query parameters spec as per RFC
    params: Dict
    url: str
    data: BufferedIOBase
    json: Dict


@dataclass(frozen=True, init=True)
class JsonRequest(Request):
    """
    Request expecting JSON as a response
    """
    pass


@dataclass(frozen=True)
class StreamRequest(Request):
    """
    Request expecting binary stream as a response
    """
    pass


@dataclass(frozen=True)
class PlainRequest(Request):
    """
    Request expecting plain text a response
    """
    pass


async def session(token: Optional[str] = None):
    async def trace(session, trace_config_ctx, params):  # pragma: no cover
        log.debug(f'{params}')

    trace_config = aiohttp.TraceConfig()

    if log.getEffectiveLevel() == logging.DEBUG:  # pragma: no cover
        trace_config.on_request_start.append(trace)
        trace_config.on_response_chunk_received.append(trace)
        trace_config.on_request_chunk_sent.append(trace)
        trace_config.on_request_end.append(trace)

    _default_auth_headers = {'Authorization': f'Bearer {token}'} if token \
        else {}

    _session = aiohttp.ClientSession(trace_configs=[trace_config],
                                     headers=_default_auth_headers,
                                     )

    return _session


class SyncStreamWrapper(AbstractContextManager):
    def __init__(self, context, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        self._loop = loop
        self._context = context
        self._stream_reader = None

    def __enter__(self):
        self._stream_reader = self._run_sync(
            self._context.__aenter__()).content
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self._run_sync(self._context.__aexit__(
            exc_type, exc_value, traceback
        ))

    def _run_sync(self, coro):
        return self._loop.run_until_complete(coro)

    def readable(self):
        return True

    def readinto(self, buf):
        chunk = self._run_sync(self._stream_reader.read(len(buf)))
        log.debug(f'chunk size={len(chunk)}')
        BytesIO(chunk).readinto(buf)

        return len(chunk)

    @property
    def closed(self):
        return False

    def read(self):
        return self._run_sync(self._stream_reader.readany())


@asynccontextmanager
async def _fetch(request: Request, session, url: str):
    async with session.request(
            method=request.method,
            params=request.params,
            url=url + request.url,
            data=request.data,
            json=request.json) as resp:
        try:
            resp.raise_for_status()
        except aiohttp.ClientResponseError as error:
            code = error.status
            message = error.message
            try:
                error_response = await resp.json()
                # TODO(artyom 07/13/2018): API should return error text
                # in HTTP Reason Phrase
                # (https://tools.ietf.org/html/rfc2616#section-6.1.1)
                message = error_response['error']
            except Exception:
                pass
            if code == 400:
                raise BadRequestError(message)
            if code == 401:
                raise UnauthorizedError(message)
            if code == 403:
                raise AccessDeniedError(message)
            elif code == 404:
                raise NotFoundError(message)
            elif code == 405:
                raise MethodNotAllowedError(error)
            raise BadRequestError(message) from error

        yield resp


@singledispatch
async def fetch(request, session, url: str):
    raise NotImplementedError(
        f'Unknown request type: {type(request)}')  # pragma: no cover


@fetch.register(JsonRequest)
async def _(request, session, url: str):
    async with _fetch(request, session, url) as resp:
        return await resp.json()


@fetch.register(PlainRequest)  # NOQA
async def _(request, session, url: str):
    async with _fetch(request, session, url) as resp:
        return await resp.text()


@fetch.register(StreamRequest)  # NOQA
async def _(request, session, url: str):
    return SyncStreamWrapper(context=_fetch(request, session, url))
