from builtins import FileNotFoundError as BuiltinFileNotFoundError
from contextlib import contextmanager
from io import BufferedReader, BytesIO
from typing import List

from dataclasses import dataclass

from .client import AccessDeniedError as AuthAccessDeniedError
from .client import ApiClient, ClientError
from .client import FileNotFoundError as ClientFileNotFoundError
from .requests import (CreateRequest, DeleteRequest, ListRequest,
                       MkDirsRequest, OpenRequest, Request)


class StorageError(ClientError):
    pass


class FileNotFoundError(StorageError, BuiltinFileNotFoundError):
    pass


class AccessDeniedError(StorageError, AuthAccessDeniedError):
    pass


@dataclass(frozen=True)
class FileStatus:
    path: str
    size: int
    # TODO (R Zubairov) Make a enum
    type: str


class Storage(ApiClient):

    def _fetch_sync(self, request: Request):
        try:
            return super(Storage, self)._fetch_sync(request)
        except AuthAccessDeniedError as error:
            raise AccessDeniedError(error)
        except ClientFileNotFoundError as error:
            raise FileNotFoundError(error)

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

    @contextmanager
    def open(self, *, path: str) -> BytesIO:
        with self._fetch_sync(OpenRequest(path=path)) as content:
            yield BufferedReader(content)

    def rm(self, *, path: str) -> str:
        self._fetch_sync(DeleteRequest(path=path))
        return path
