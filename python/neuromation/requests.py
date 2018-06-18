import json

import aiohttp
from dataclasses import asdict, dataclass


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


async def session():
    return aiohttp.ClientSession()


def route_method(request: Request):
    if type(request) is JobStatusRequest:
        return '/jobs', 'GET'
    elif type(request) is TrainRequest:
        return '/train', 'POST'
    elif type(request) is InferRequest:
        return '/infer', 'POST'
    else:
        raise TypeError(f'Unknown request type: {type(request)}')


async def fetch(session, url: str, request: Request):
    route, method = route_method(request)
    async with session.request(
                method=method,
                url=url + route,
                json=asdict(request)) as resp:
        return json.loads(resp.text)
