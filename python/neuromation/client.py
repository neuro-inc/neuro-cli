import asyncio
import re

from dataclasses import dataclass

from .requests import (Image, InferRequest, JobStatusRequest, ResourcesPayload,
                       TrainRequest, fetch, session)


def parse_memory(memory) -> int:
    """Parse string expression i.e. 16M, 16MB, etc
    M = 1024 * 1024, MB = 1000 * 1000

    returns value in bytes"""

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
                        resources=ResourcesPayload(
                            memory_mb=to_megabytes(resources.memory),
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
                        resources=ResourcesPayload(
                            memory_mb=to_megabytes(resources.memory),
                            cpu=resources.cpu,
                            gpu=resources.gpu),
                        dataset_storage_uri=dataset,
                        result_storage_uri=results))))


class Storage:
    pass
