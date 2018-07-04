import asyncio
import logging
from io import BytesIO
from typing import ClassVar, List

import aiohttp
from dataclasses import asdict, dataclass

log = logging.getLogger(__name__)


class RequestError(Exception):
    pass


@dataclass(frozen=True)
class ResourcesPayload:
    memory_mb: str
    cpu: int
    gpu: int


@dataclass(frozen=True)
class Image:
    image: str
    command: str


class Request:
    pass


@dataclass(frozen=True)
class JobStatusRequest(Request):
    id: str


@dataclass(frozen=True)
class InferRequest(Request):
    image: Image
    dataset_storage_uri: str
    result_storage_uri: str
    model_storage_uri: str
    resources: ResourcesPayload


@dataclass(frozen=True)
class TrainRequest(Request):
    resources: ResourcesPayload
    image: Image
    dataset_storage_uri: str
    result_storage_uri: str


@dataclass(frozen=True)
class StorageRequest(Request):
    pass


@dataclass(frozen=True)
class MkDirsRequest(StorageRequest):
    op: ClassVar[str] = 'MKDIRS'
    paths: List[str]
    root: str


@dataclass(frozen=True)
class ListRequest(StorageRequest):
    op: ClassVar[str] = 'LISTSTATUS'
    path: str


@dataclass(frozen=True)
class CreateRequest(StorageRequest):
    op: ClassVar[str] = 'CREATE'
    path: str
    data: BytesIO


@dataclass(frozen=True)
class OpenRequest(StorageRequest):
    op: ClassVar[str] = 'OPEN'
    path: str


@dataclass(frozen=True)
class DeleteRequest(StorageRequest):
    op: ClassVar[str] = 'DELETE'
    path: str


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


def route_method(request: Request):
    def join_url_path(a: str, b: str) -> str:
        return '/' + '/'.join(
            segment for segment in
            a.split('/') + b.split('/')
            if segment
        )

    if isinstance(request, JobStatusRequest):
        return '/jobs', None, 'GET', asdict(request), None
    elif isinstance(request, TrainRequest):
        return '/train', None, 'POST', asdict(request), None
    elif isinstance(request, InferRequest):
        return '/infer', None, 'POST', asdict(request), None
    elif isinstance(request, CreateRequest):
        return (
            join_url_path('/storage', request.path),
            None, 'PUT', None, request.data)
    elif isinstance(request, MkDirsRequest):
        return (
            join_url_path('/storage', request.root),
            request.op, 'PUT', request.paths, None)
    elif isinstance(request, ListRequest):
        return (
            join_url_path('/storage', request.path),
            request.op, 'GET', None, None)
    elif isinstance(request, OpenRequest):
        return (
            join_url_path('/storage', request.path),
            None, 'GET', None, None)
    elif isinstance(request, DeleteRequest):
        return (
            join_url_path('/storage', request.path),
            None, 'DELETE', None, None)
    else:
        raise TypeError(f'Unknown request type: {type(request)}')


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
    route, params, method, json, data = route_method(request)
    _url = url + route

    log.debug(f'Routing request {request}')
    log.debug(f'route={route} params={params}, method={method}, json={json}, data={data}')  # NOQA
    log.debug(f'url={_url}')

    async with session.request(
                method=method,
                params=params,
                url=_url,
                data=data,
                json=json) as resp:

        try:
            resp.raise_for_status()
        except aiohttp.ClientError as error:
            # Refactor the whole method and
            # split binary and non-binary responses
            if resp.content_type == 'application/json':
                error = await resp.json()
                raise RequestError(error['error'])
            raise RequestError(error.message)

        if resp.content_type == 'application/json':
            return await resp.json()

        # TODO (artyom, 06/22/2018): refactor this. right now it is
        # returning two different types
        return SyncStreamWrapper(resp.content)
