import asyncio

from dataclasses import dataclass

from neuromation.strings import parse

from .client import ApiClient
from .requests import (ContainerPayload, InferRequest, JobStatusRequest,
                       ResourcesPayload, TrainRequest)


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
                    container=ContainerPayload(
                        image=image.image,
                        command=image.command,
                        resources=ResourcesPayload(
                            memory_mb=parse.to_megabytes(resources.memory),
                            cpu=float(resources.cpu),
                            gpu=float(resources.gpu))),
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
                container=ContainerPayload(
                    image=image.image,
                    command=image.command,
                    resources=ResourcesPayload(
                        memory_mb=parse.to_megabytes(resources.memory),
                        cpu=float(resources.cpu),
                        gpu=float(resources.gpu))),
                dataset_storage_uri=dataset,
                result_storage_uri=results))

        return JobStatus(
            **res,
            client=self)
