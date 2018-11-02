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
    # TODO (A Yushkovskiy) I think we should use the same 'FileStatus' class
    # from platform_storage_api (extracted to a separate project 'platform-common')
    # related: https://github.com/neuromation/platform-storage-api/issues/49
    type: str
    modification_time: Optional[int] = None
    permission: Optional[str] = None

    @classmethod
    def from_prmitive(
        cls,
        path: str,
        type: str,
        length: int,
        modificationTime: Optional[int] = None,
        permission: Optional[str] = None,
    ) -> "FileStatus":
        return cls(
            path=path,
            type=type,
            size=length,
            modification_time=modificationTime,
            permission=permission,
        )


class Storage(ApiClient):
    def ls(self, *, path: str) -> List[FileStatus]:
        def get_file_status_list(response: Dict[str, Any]) -> List[Dict[str, Any]]:
            return response["FileStatuses"]["FileStatus"]

        response_dict = self._fetch_sync(ListRequest(path=path))
        result: List[FileStatus] = list()
        if response_dict:
            result.extend(
                FileStatus.from_prmitive(**status)
                for status in get_file_status_list(response_dict)
            )
        return result

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
