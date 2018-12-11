import logging
from dataclasses import dataclass
from io import BytesIO
from typing import Any, ClassVar, Dict, List, Optional

from neuromation import http
from neuromation.http import JsonRequest


log = logging.getLogger(__name__)


def add_path(prefix: str, path: str) -> str:
    # ('/prefix', 'dir') and ('/prefix', '/dir')
    # are semantically the same in case of build
    # file Storage API calls
    return prefix + path.strip("/")


class RequestError(Exception):
    pass


@dataclass(frozen=True)
class Request:
    pass


@dataclass(frozen=True)
class ResourcesPayload:
    memory_mb: str
    cpu: float
    gpu: Optional[int]
    gpu_model: Optional[str]
    shm: Optional[bool]

    def to_primitive(self) -> Dict[str, Any]:
        value = {"memory_mb": self.memory_mb, "cpu": self.cpu, "shm": self.shm}
        if self.gpu:
            value["gpu"] = self.gpu
            value["gpu_model"] = self.gpu_model
        return value


@dataclass(frozen=True)
class ContainerPayload:
    image: str
    command: Optional[str]
    http: Optional[Dict[str, int]]
    ssh: Optional[Dict[str, int]]
    resources: ResourcesPayload

    def to_primitive(self) -> Dict[str, Any]:
        primitive = {"image": self.image, "resources": self.resources.to_primitive()}
        if self.command:
            primitive["command"] = self.command
        if self.http:
            primitive["http"] = self.http
        if self.ssh:
            primitive["ssh"] = self.ssh
        return primitive


@dataclass(frozen=True)
class JobStatusRequest(Request):
    id: str


@dataclass(frozen=True)
class ShareResourceRequest(Request):
    whom: str
    # List of { uri: '...', action: '...' }
    permissions: List[Dict[str, str]]

    def to_http_request(self) -> http.Request:
        return http.PlainRequest(
            url=f"/users/{self.whom}/permissions",
            params=None,
            headers=None,
            method="POST",
            json=self.permissions,
            data=None,
        )


@dataclass(frozen=True)
class TrainRequest(Request):
    container: ContainerPayload
    dataset_storage_uri: str
    result_storage_uri: str
    description: Optional[str]

    def to_primitive(self) -> Dict[str, Any]:
        json_params: Dict[str, Any] = {
            "container": self.container.to_primitive(),
            "dataset_storage_uri": self.dataset_storage_uri,
            "result_storage_uri": self.result_storage_uri,
        }

        if self.description:
            json_params["description"] = self.description
        return json_params

    def to_http_request(self) -> JsonRequest:
        json_params = self.to_primitive()
        return http.JsonRequest(
            url="/models", params=None, method="POST", json=json_params, data=None
        )


@dataclass(frozen=True)
class JobRequest(Request):
    pass


@dataclass(frozen=True)
class JobListRequest(JobRequest):
    pass


@dataclass(frozen=True)
class StorageRequest(Request):
    def to_http_request(self) -> http.Request:  # pragma: no cover
        raise NotImplementedError


@dataclass(frozen=True)
class MkDirsRequest(StorageRequest):
    op: ClassVar[str] = "MKDIRS"
    path: str

    def to_http_request(self) -> http.Request:
        return http.PlainRequest(
            url=add_path("/storage/", self.path),
            params=self.op,
            method="PUT",
            json=None,
            data=None,
        )


@dataclass(frozen=True)
class RenameRequest(StorageRequest):
    op: ClassVar[str] = "RENAME"
    src_path: str
    dst_path: str

    def to_http_request(self) -> http.Request:
        return http.JsonRequest(
            url=add_path("/storage/", self.src_path),
            params={"op": self.op, "destination": self.dst_path},
            method="POST",
            json=None,
            data=None,
        )


@dataclass(frozen=True)
class ListRequest(StorageRequest):
    op: ClassVar[str] = "LISTSTATUS"
    path: str


@dataclass(frozen=True)
class FileStatRequest(StorageRequest):
    op: ClassVar[str] = "GETFILESTATUS"
    path: str

    def to_http_request(self) -> http.Request:
        return http.JsonRequest(
            url=add_path("/storage/", self.path),
            params=self.op,
            method="GET",
            json=None,
            data=None,
        )


@dataclass(frozen=True)
class CreateRequest(StorageRequest):
    op: ClassVar[str] = "CREATE"
    path: str
    data: BytesIO


@dataclass(frozen=True)
class OpenRequest(StorageRequest):
    op: ClassVar[str] = "OPEN"
    path: str


@dataclass(frozen=True)
class DeleteRequest(StorageRequest):
    op: ClassVar[str] = "DELETE"
    path: str


# TODO: better polymorphism?
def build(request: Request) -> http.Request:

    if isinstance(request, JobStatusRequest):
        return http.JsonRequest(
            url=f"/jobs/{request.id}", params=None, method="GET", json=None, data=None
        )
    elif isinstance(request, JobListRequest):
        return http.JsonRequest(
            url="/jobs", params=None, method="GET", json=None, data=None
        )
    elif isinstance(request, TrainRequest):
        return request.to_http_request()
    elif isinstance(request, CreateRequest):
        return http.PlainRequest(
            url=add_path("/storage/", request.path),
            params=None,
            method="PUT",
            json=None,
            data=request.data,
        )
    elif isinstance(request, MkDirsRequest):
        return request.to_http_request()
    elif isinstance(request, RenameRequest):
        return request.to_http_request()
    elif isinstance(request, FileStatRequest):
        return request.to_http_request()
    elif isinstance(request, ListRequest):
        return http.JsonRequest(
            url=add_path("/storage/", request.path),
            params=request.op,
            method="GET",
            json=None,
            data=None,
        )
    elif isinstance(request, OpenRequest):
        return http.StreamRequest(
            url=add_path("/storage/", request.path),
            params=None,
            method="GET",
            json=None,
            data=None,
        )
    elif isinstance(request, DeleteRequest):
        return http.PlainRequest(
            url=add_path("/storage/", request.path),
            params=None,
            method="DELETE",
            json=None,
            data=None,
        )
    elif isinstance(request, ShareResourceRequest):
        return request.to_http_request()
    else:
        raise TypeError(f"Unknown request type: {type(request)}")
