import asyncio
from io import BytesIO
from typing import List

from dataclasses import InitVar, dataclass

from .requests import (CreateRequest, DeleteRequest, Image, InferRequest,
                       JobStatusRequest, ListRequest, MkDirsRequest,
                       OpenRequest, Request, Resources, TrainRequest, fetch,
                       session)


class ApiCallError(Exception):
    pass


class ApiClient:
    def __init__(self, url: str, *, loop=None):
        self._url = url
        self._loop = loop if loop else asyncio.get_event_loop()
        self._session = self._loop.run_until_complete(session())

    async def close(self):
        if self._session.closed:
            return

        await self._session.close()
        self._session = None

    async def _fetch(self, request: Request):
        res = await fetch(session=self._session, url=self._url, request=request)
        if type(res) is dict and 'error' in res:
            raise ApiCallError(res['error'])
        return res

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
            return self.client._loop.run_until_complete(
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
                    resources=Resources(
                        memory=resources.memory,
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
                resources=resources,
                dataset_storage_uri=dataset,
                result_storage_uri=results))

        return JobStatus(
            **res,
            client=self)


@dataclass(frozen=True)
class StorageStatus:
    path: str
    size: int
    type: str


class Storage(ApiClient):
    def ls(self, *, path: str) -> str:
        return [
            StorageStatus(**status)
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
        return BytesIO(self._loop.run_until_complete(content.read()))

    def rm(self, *, path: str) -> str:
        self._fetch_sync(DeleteRequest(path=path))
        return path
