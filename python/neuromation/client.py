import asyncio
import re

from dataclasses import dataclass

from .requests import (Image, InferRequest, JobStatusRequest, Resources,
                       TrainRequest, fetch, session)


@dataclass(frozen=True)
class Resources:
    memory: str
    cpu: int
    gpu: int


@dataclass(frozen=True)
class Image:
    image: str
    command: str


@dataclass(frozen=True)
class JobStatus:
    results: str
    status: str
    id: str
    url: str
    session: object


    async def _call(self):
        return JobStatus(
                session=self.session,
                url=self.url,
                **await fetch(
                    session=self.session,
                    url=self.url,
                    request=JobStatusRequest(
                        id=self.id
                    )))

    def wait(self, timeout=None, *, loop=None):
        loop = loop if loop else asyncio.get_event_loop()

        try:
            return loop.run_until_complete(
                asyncio.wait_for(
                    self._call(),
                    timeout=timeout))
        except asyncio.TimeoutError:
            raise TimeoutError


class Model:
    def __init__(self, url, *, loop=None):
        self._url = url
        self._loop = loop if loop else asyncio.get_event_loop()
        self._session = self._loop.run_until_complete(session())


    @property
    def session(self):
        return self._session

    async def close(self):
        if self._session.closed:
            return

        await self._session.close()
        self._session = None

    def infer(
            self,
            *,
            image: Image,
            resources: Resources,
            model: str,
            dataset: str,
            results: str)-> JobStatus:
        return JobStatus(
            url=self._url,
            session=self._session,
            **self._loop.run_until_complete(
                fetch(
                    self._session,
                    self._url,
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
                        result_storage_uri=results))))

    def train(
            self,
            *,
            image: Image,
            resources: Resources,
            dataset: str,
            results: str) -> JobStatus:
        return JobStatus(
            session=self._session,
            url=self._url,
            **self._loop.run_until_complete(
                fetch(
                    self._session,
                    self._url,
                    TrainRequest(
                        image=Image(
                            image=image.image,
                            command=image.command),
                        resources=resources,
                        dataset_storage_uri=dataset,
                        result_storage_uri=results))))


class Storage:
    pass
