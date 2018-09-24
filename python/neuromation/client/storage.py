from contextlib import contextmanager
from io import BufferedReader, BytesIO
from typing import List

from dataclasses import dataclass

from .client import ApiClient
from .requests import (CreateRequest, CreateRequestArchived, DeleteRequest,
                       ListRequest, MkDirsRequest, OpenRequest)


@dataclass(frozen=True)
class FileStatus:
    path: str
    size: int
    # TODO (R Zubairov) Make a enum
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

    def create_archived_on_fly(self, *, path: str, data: BytesIO) -> str:
        self._fetch_sync(CreateRequestArchived(path=path, data=data))
        return path

    @contextmanager
    def open(self, *, path: str) -> BytesIO:
        with self._fetch_sync(OpenRequest(path=path)) as content:
            yield BufferedReader(content)

    def rm(self, *, path: str) -> str:
        self._fetch_sync(DeleteRequest(path=path))
        return path
