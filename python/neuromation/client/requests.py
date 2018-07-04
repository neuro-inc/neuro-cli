import logging
from io import BytesIO
from typing import ClassVar, List

from dataclasses import asdict, dataclass

from neuromation import http

log = logging.getLogger(__name__)


class RequestError(Exception):
    pass


class Request:
    pass


@dataclass(frozen=True)
class ResourcesPayload:
    memory_mb: str
    cpu: int
    gpu: int


@dataclass(frozen=True)
class ImagePayload:
    image: str
    command: str


@dataclass(frozen=True)
class JobStatusRequest(Request):
    id: str


@dataclass(frozen=True)
class InferRequest(Request):
    image: ImagePayload
    dataset_storage_uri: str
    result_storage_uri: str
    model_storage_uri: str
    resources: ResourcesPayload


@dataclass(frozen=True)
class TrainRequest(Request):
    resources: ResourcesPayload
    image: ImagePayload
    dataset_storage_uri: str
    result_storage_uri: str


@dataclass(frozen=True)
class StorageRequest(Request):
    pass


@dataclass(frozen=True)
class MkDirsRequest(StorageRequest):
    op: ClassVar[str] = 'MKDIRS'
    path: str


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


# TODO: better polymorphism?
def build(request: Request) -> http.Request:
    def join_url_path(a: str, b: str) -> str:
        return '/' + '/'.join(
            segment for segment in
            a.split('/') + b.split('/')
            if segment
            )

    if isinstance(request, JobStatusRequest):
        return http.Request(
            url='/jobs',
            params=None,
            method='GET',
            json=asdict(request),
            data=None)
    elif isinstance(request, TrainRequest):
        return http.Request(
            url='/train',
            params=None,
            method='POST',
            json=asdict(request),
            data=None)
    elif isinstance(request, InferRequest):
        return http.Request(
            url='/infer',
            params=None,
            method='POST',
            json=asdict(request),
            data=None)
    elif isinstance(request, CreateRequest):
        return http.Request(
            url=join_url_path('/storage', request.path),
            params=None,
            method='PUT',
            json=None,
            data=request.data)
    elif isinstance(request, MkDirsRequest):
        return http.Request(
            url=join_url_path('/storage', request.path),
            params=request.op,
            method='PUT',
            json=None,
            data=None)
    elif isinstance(request, ListRequest):
        return http.Request(
            url=join_url_path('/storage', request.path),
            params=request.op,
            method='GET',
            json=None,
            data=None)
    elif isinstance(request, OpenRequest):
        return http.Request(
            url=join_url_path('/storage', request.path),
            params=None,
            method='GET',
            json=None,
            data=None)
    elif isinstance(request, DeleteRequest):
        return http.Request(
            url=join_url_path('/storage', request.path),
            params=None,
            method='DELETE',
            json=None,
            data=None)
    else:
        raise TypeError(f'Unknown request type: {type(request)}')
