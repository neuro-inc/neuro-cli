from contextlib import contextmanager
from dataclasses import dataclass
from io import BufferedReader, BytesIO
from typing import Any, Dict, Iterator, List, Optional

from neuromation.http.fetch import FetchError

from .client import ApiClient
from .requests import (
    CreateRequest,
    DeleteRequest,
    ListRequest,
    MkDirsRequest,
    OpenRequest,
)


@dataclass(frozen=True)
class FileStatus:
    path: str
    size: int
    # TODO (R Zubairov) Make a enum
    type: str
    modification_time: int
    permission: str

    @classmethod
    def from_primitive(cls, **values) -> "FileStatus":
        return cls(
            path=values["path"],
            type=values["type"],
            size=int(values["length"]),
            modification_time=int(values["modificationTime"]),
            permission=values["permission"],
        )


class Storage(ApiClient):
    def ls(self, *, path: str) -> List[FileStatus]:
        def get_file_status_list(response: Dict[str, Any]) -> List[Dict[str, Any]]:
            return response["FileStatuses"]["FileStatus"]

        response_dict = self._fetch_sync(ListRequest(path=path))
        return [
            FileStatus.from_primitive(**status)
            for status in get_file_status_list(response_dict)
        ]

    def mkdirs(self, *, path: str) -> str:
        self._fetch_sync(MkDirsRequest(path=path))
        return path

    def create(self, *, path: str, data: BytesIO) -> str:
        self._fetch_sync(CreateRequest(path=path, data=data))
        return path

    @contextmanager
    def open(self, *, path: str) -> Iterator[BufferedReader]:
        try:
            with self._fetch_sync(OpenRequest(path=path)) as content:
                yield BufferedReader(content)
        except FetchError as error:
            error_class = type(error)
            mapped_class = self._exception_map.get(error_class, error_class)
            raise mapped_class(error) from error

    def rm(self, *, path: str) -> str:
        self._fetch_sync(DeleteRequest(path=path))
        return path
