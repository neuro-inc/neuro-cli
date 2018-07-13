import asyncio
import logging
import sys
from contextlib import AbstractContextManager
from functools import singledispatch
from io import BufferedIOBase, BytesIO
from typing import Dict

import aiohttp
from dataclasses import dataclass

log = logging.getLogger(__name__)


class FetchError(Exception):
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


class JsonRequest(Request):
    """
    Request expecting JSON as a response
    """
    pass


class StreamRequest(Request):
    """
    Request expecting binary stream as a response
    """
    pass


class PlainRequest(Request):
    """
    Request expecting plain text a response
    """
    pass


async def session():
    async def trace(session, trace_config_ctx, params):
        log.debug(f'{params}')

    trace_config = aiohttp.TraceConfig()

    if log.getEffectiveLevel() == logging.DEBUG:
        trace_config.on_request_start.append(trace)
        trace_config.on_response_chunk_received.append(trace)
        trace_config.on_request_chunk_sent.append(trace)
        trace_config.on_request_end.append(trace)

    _session = aiohttp.ClientSession(trace_configs=[trace_config])

    return _session


class SyncStreamWrapper(AbstractContextManager):
    def __init__(self, stream_reader, context, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        self._loop = loop
        self._context = context
        self._stream_reader = stream_reader

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


async def _fetch(request: Request, session, url: str):
    context = session.request(
                method=request.method,
                params=request.params,
                url=url + request.url,
                data=request.data,
                json=request.json)
    resp = await context.__aenter__()

    try:
        resp.raise_for_status()
    except aiohttp.ClientError as error:
        message = error.message

        try:
            error = await resp.json()
            # TODO(artyom 07/13/2018): API should return error text
            # in HTTP Reason Phrase
            # (https://tools.ietf.org/html/rfc2616#section-6.1.1)
            message = error['error']
        finally:
            await context.__aexit__(*sys.exc_info())

        raise FetchError(message)

    return resp, context


@singledispatch
async def fetch(request, session, url: str):
    raise NotImplementedError(f'Unknown request type: {type(request)}')


@fetch.register(JsonRequest)
async def _(request, session, url: str):
    resp, context = await _fetch(request, session, url)

    try:
        return await resp.json()
    finally:
        await context.__aexit__(*sys.exc_info())


@fetch.register(PlainRequest)  # NOQA
async def _(request, session, url: str):
    resp, context = await _fetch(request, session, url)

    try:
        return await resp.text()
    finally:
        await context.__aexit__(*sys.exc_info())


@fetch.register(StreamRequest)  # NOQA
async def _(request, session, url: str):
    resp, context = await _fetch(request, session, url)
    return SyncStreamWrapper(stream_reader=resp.content, context=context)
