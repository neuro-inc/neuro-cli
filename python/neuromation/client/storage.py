from io import BufferedReader, BytesIO
from typing import List

from dataclasses import dataclass

from .client import ApiClient
from .requests import (CreateRequest, DeleteRequest, ListRequest,
                       MkDirsRequest, OpenRequest)


@dataclass(frozen=True)
class FileStatus:
    path: str
    size: int
    type: str


class Storage(ApiClient):
    def ls(self, *, path: str) -> List[FileStatus]:
        return [
            FileStatus(**status)
            for status in
            self._fetch_sync(ListRequest(path=path))
        ]

    def mkdirs(self, *, path: List[str]) -> List[str]:
        self._fetch_sync(MkDirsRequest(path=path))
        return path

    def create(self, *, path: str, data: BytesIO) -> str:
        self._fetch_sync(CreateRequest(path=path, data=data))
        return path

    def open(self, *, path: str) -> BytesIO:
        content = self._fetch_sync(OpenRequest(path=path))
        return BufferedReader(content)

    def rm(self, *, path: str) -> str:
        self._fetch_sync(DeleteRequest(path=path))
        return path
