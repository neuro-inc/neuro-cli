import asyncio

from dataclasses import dataclass, replace


@dataclass
class Resources:
    memory: str
    cpu: int
    gpu: int


@dataclass
class JobStatus:
    results: str
    status: str
    id: str

    async def _worker(self):
        await asyncio.sleep(0.1)
        return replace(self, status='FINISHED')

    def wait(self, timeout=None, *, loop=None):
        loop = loop if loop else asyncio.get_event_loop()

        try:
            return loop.run_until_complete(
                asyncio.wait_for(
                    self._worker(),
                    timeout=timeout))
        except asyncio.TimeoutError:
            raise TimeoutError


class Model:
    def __init__(self, url):
        self._url = url

    def infer(
            self,
            image: str,
            resources: Resources,
            model: str,
            dataset: str,
            results: str)-> JobStatus:
        return JobStatus(
                results=results,
                status='RUNNING',
                id='foo')

    def train(
            self,
            image: str,
            resources: Resources,
            dataset: str,
            results: str) -> JobStatus:
        return JobStatus(
            results=results,
            status='RUNNING',
            id='foo')


class Storage:
    pass
    # def __init__(self, url):
    #     self._url = url
