import asyncio
import re
from io import BufferedReader, BytesIO
from typing import List

from dataclasses import dataclass

from .requests import (CreateRequest, DeleteRequest, Image, InferRequest,
                       JobStatusRequest, ListRequest, MkDirsRequest,
                       OpenRequest, Request, RequestError, ResourcesPayload,
                       TrainRequest, fetch, session)


def parse_memory(memory) -> int:
    """Parse string expression i.e. 16M, 16MB, etc
    M = 1024 * 1024, MB = 1000 * 1000

    returns value in bytes"""

    # Mega, Giga, Tera, etc
    prefixes = 'MGTPEZY'
    value_error = ValueError(f'Unable parse value: {memory}')

    if not memory:
        raise value_error

    pattern = \
        r'^(?P<value>\d+)(?P<units>(kB|K)|((?P<prefix>[{prefixes}])(?P<unit>B?)))$'.format(  # NOQA
            prefixes=prefixes
        )
    regex = re.compile(pattern)
    match = regex.fullmatch(memory)

    if not match:
        raise value_error

    groups = match.groupdict()

    value = int(groups['value'])
    unit = groups['unit']
    prefix = groups['prefix']
    units = groups['units']

    if units == 'kB':
        return value * 1000

    if units == 'K':
        return value * 1024

    # Our prefix string starts with Mega
    # so for index 0 the power should be 2
    power = 2 + prefixes.index(prefix)
    multiple = 1000 if unit else 1024

    return value * multiple ** power


def to_megabytes(value: str) -> int:
    return int(parse_memory(value) / (1024 ** 2))


@dataclass(frozen=True)
class Resources:
    memory: str
    cpu: int
    gpu: int


class ApiError(Exception):
    pass


class ApiClient:
    def __init__(self, url: str, *, loop=None):
        self._url = url
        self._loop = loop if loop else asyncio.get_event_loop()
        self._session = self.loop.run_until_complete(session())

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.loop.run_until_complete(self.close())

    @property
    def loop(self):
        return self._loop

    async def close(self):
        if self._session and self._session.closed:
            return

        await self._session.close()
        self._session = None

    async def _fetch(self, request: Request):
        try:
            return await fetch(
                session=self._session,
                url=self._url,
                request=request)
        except RequestError as error:
            raise ApiError(f'{error}')

    def _fetch_sync(self, request: Request):
        return self._loop.run_until_complete(self._fetch(request))


@dataclass(frozen=True)
class JobStatus:
    results: str
    status: str
    id: str
    client: ApiClient

    async def _call(self):
        return JobStatus(
                client=self.client,
                **await self.client._fetch(
                    request=JobStatusRequest(
                        id=self.id
                    )))

    def wait(self, timeout=None):
        try:
            return self.client.loop.run_until_complete(
                asyncio.wait_for(
                    self._call(),
                    timeout=timeout
                    )
                )
        except asyncio.TimeoutError:
            raise TimeoutError


class Model(ApiClient):
    def infer(
            self,
            *,
            image: Image,
            resources: Resources,
            model: str,
            dataset: str,
            results: str)-> JobStatus:
        res = self._fetch_sync(
                InferRequest(
                    image=Image(
                        image=image.image,
                        command=image.command),
                    resources=ResourcesPayload(
                        memory_mb=to_megabytes(resources.memory),
                        cpu=resources.cpu,
                        gpu=resources.gpu),
                    model_storage_uri=model,
                    dataset_storage_uri=dataset,
                    result_storage_uri=results))

        return JobStatus(
            **res,
            client=self)

    def train(
            self,
            *,
            image: Image,
            resources: Resources,
            dataset: str,
            results: str) -> JobStatus:
        res = self._fetch_sync(
            TrainRequest(
                image=Image(
                    image=image.image,
                    command=image.command),
                resources=ResourcesPayload(
                    memory_mb=to_megabytes(resources.memory),
                    cpu=resources.cpu,
                    gpu=resources.gpu),
                dataset_storage_uri=dataset,
                result_storage_uri=results))

        return JobStatus(
            **res,
            client=self)


@dataclass(frozen=True)
class FileStatus:
    path: str
    size: int
    type: str


class Storage(ApiClient):
    def ls(self, *, path: str) -> List[FileStatus]:
        return [
            FileStatus(**status)
            for status in
            self._fetch_sync(ListRequest(path=path))
        ]

    def mkdirs(self, *, root: str, paths: List[str]) -> List[str]:
        self._fetch_sync(MkDirsRequest(root=root, paths=paths))
        return paths

    def create(self, *, path: str, data: BytesIO) -> str:
        self._fetch_sync(CreateRequest(path=path, data=data))
        return path

    def open(self, *, path: str) -> BytesIO:
        content = self._fetch_sync(OpenRequest(path=path))
        return BufferedReader(content)

    def rm(self, *, path: str) -> str:
        self._fetch_sync(DeleteRequest(path=path))
        return path
