import json

import aiohttp
from dataclasses import asdict, dataclass


class Request:
    def __init__(self, route: str, method: str):
        self._route = route
        self._method = method

    @property
    def method(self):
        return self._method

    @property
    def route(self):
        return self._route


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
class JobStatusRequest(Request):
    id: str

    def __post_init__(self):
        super().__init__(route='/jobs', method='GET')


@dataclass
class InferRequest(Request):
    image: Image
    dataset_storage_uri: str
    result_storage_uri: str
    model_storage_uri: str
    resources: Resources

    def __post_init__(self):
        """ dataclass' auto-generated __init__ will call this method"""
        super().__init__(route='/infer', method='POST')


@dataclass
class TrainRequest(Request):
    resources: Resources
    image: Image
    dataset_storage_uri: str
    result_storage_uri: str

    def __post_init__(self):
        """ dataclass' auto-generated __init__ will call this method"""
        super().__init__(route='/train', method='POST')


async def fetch(url: str, request: Request):
    async with aiohttp.ClientSession() as session:
        func = None

        if request.method == 'POST':
            func = session.post
        elif request.method == 'GET':
            func = session.get
        else:
            raise ValueError(f'Invalid HTTP call method: {request.method}')

        async with func(
                    url=url + request.route,
                    json=asdict(request)) as resp:
            return json.loads(resp.text)
