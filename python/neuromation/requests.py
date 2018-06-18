import json
from io import BytesIO
from typing import ClassVar, List

import aiohttp
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Resources:
    memory: str
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
    resources: Resources


@dataclass(frozen=True)
class TrainRequest(Request):
    resources: Resources
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
    return aiohttp.ClientSession()


def route_method(request: Request):
    if type(request) is JobStatusRequest:
        return '/jobs', None, 'GET', asdict(request), None
    elif type(request) is TrainRequest:
        return '/train', None, 'POST', asdict(request), None
    elif type(request) is InferRequest:
        return '/infer', None, 'POST', asdict(request), None
    elif type(request) is CreateRequest:
        return '/storage/' + request.path, None, 'PUT', None, request.data
    elif type(request) is MkDirsRequest:
        return '/storage/' + request.root, {request.op: None}, 'PUT', request.paths, None
    elif type(request) is ListRequest:
        return '/storage', {request.op: None ,**asdict(request)}, 'GET', None, None
    elif type(request) is OpenRequest:
        return '/storage/' + request.path, None, 'GET', None, None
    elif type(request) is DeleteRequest:
        return '/storage/' + request.path, None, 'DELETE', None, None
    else:
        raise TypeError(f'Unknown request type: {type(request)}')


async def fetch(session, url: str, request: Request):
        route, params, method, json, data = route_method(request)
        async with session.request(
                    method=method,
                    params=params,
                    url=url + route,
                    data=data,
                    json=json) as resp:
            if resp.content_type == 'application/json':
                return await resp.json()
            # TODO (artyom, 06/17/2018): support chunks
            return resp
