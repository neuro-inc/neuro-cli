import asyncio

from dataclasses import dataclass

from neuromation import requests

from .requests import InferRequest, TrainRequest, fetch


@dataclass
class Resources:
    memory: str
    cpu: int
    gpu: int


@dataclass
class Image:
    image: str
    CMD: str  # NOQA


@dataclass
class JobStatus:
    results: str
    status: str
    id: str
    url: str

    async def _call(self):
        return JobStatus(
                **await fetch(
                    url=self.url,
                    request=requests.JobStatusRequest(
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
    def __init__(self, url):
        self._url = url

    def infer(
            self,
            *,
            image: Image,
            resources: Resources,
            model: str,
            dataset: str,
            results: str,
            loop=None)-> JobStatus:
        loop = loop if loop else asyncio.get_event_loop()
        return JobStatus(
            url=self._url,
            **loop.run_until_complete(fetch(
                url=self._url,
                request=InferRequest(
                    image=requests.Image(
                        image=image.image,
                        CMD=image.CMD),
                    resources=requests.Resources(
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
            results: str,
            loop=None) -> JobStatus:
        loop = loop if loop else asyncio.get_event_loop()
        return JobStatus(
            url=self._url,
            **loop.run_until_complete(fetch(
                url=self._url,
                request=TrainRequest(
                    image=requests.Image(
                        image=image.image,
                        CMD=image.CMD),
                    resources=resources,
                    dataset_storage_uri=dataset,
                    result_storage_uri=results))))


class Storage:
    pass
    # def __init__(self, url):
    #     self._url = url
