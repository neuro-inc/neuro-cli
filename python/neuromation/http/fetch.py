import asyncio
import logging
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


class SyncStreamWrapper:
    def __init__(self, stream, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        self._loop = loop
        self._stream_reader = stream

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


async def fetch(session, url: str, request: Request):
    async with session.request(
                method=request.method,
                params=request.params,
                url=url + request.url,
                data=request.data,
                json=request.json) as resp:

        try:
            resp.raise_for_status()
        except aiohttp.ClientError as error:
            # Refactor the whole method and
            # split binary and non-binary responses
            if resp.content_type == 'application/json':
                error = await resp.json()
                raise FetchError(error['error'])
            raise FetchError(error.message)

        if resp.content_type == 'application/json':
            return await resp.json()

        # TODO (artyom, 06/22/2018): refactor this. right now it is
        # returning two different types
        return SyncStreamWrapper(resp.content)
