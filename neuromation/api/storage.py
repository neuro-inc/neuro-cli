import asyncio
import enum
import errno
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

import attr
from yarl import URL

from .abc import AbstractProgress
from .config import _Config
from .core import ResourceNotFound, _Core
from .url_utils import (
    _extract_path,
    normalize_local_path_uri,
    normalize_storage_path_uri,
)
from .utils import NoPublicConstructor


log = logging.getLogger(__name__)

Printer = Callable[[str], None]


class FileStatusType(str, enum.Enum):
    DIRECTORY = "DIRECTORY"
    FILE = "FILE"


@dataclass(frozen=True)
class FileStatus:
    path: str
    size: int
    type: FileStatusType
    modification_time: int
    permission: str

    def is_file(self) -> bool:
        return self.type == FileStatusType.FILE

    def is_dir(self) -> bool:
        return self.type == FileStatusType.DIRECTORY

    @property
    def name(self) -> str:
        return Path(self.path).name

    @classmethod
    def from_api(cls, values: Dict[str, Any]) -> "FileStatus":
        return cls(
            path=values["path"],
            type=FileStatusType(values["type"]),
            size=int(values["length"]),
            modification_time=int(values["modificationTime"]),
            permission=values["permission"],
        )


class Storage(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: _Config) -> None:
        self._core = core
        self._config = config

    def _uri_to_path(self, uri: URL) -> str:
        uri = normalize_storage_path_uri(uri, self._config.auth_token.username)
        prefix = uri.host + "/" if uri.host else ""
        return prefix + uri.path.lstrip("/")

    async def ls(self, uri: URL) -> List[FileStatus]:
        url = self._config.cluster_config.storage_url / self._uri_to_path(uri)
        url = url.with_query(op="LISTSTATUS")

        async with self._core.request("GET", url) as resp:
            res = await resp.json()
            return [
                FileStatus.from_api(status)
                for status in res["FileStatuses"]["FileStatus"]
            ]

    async def mkdirs(
        self, uri: URL, *, parents: bool = False, exist_ok: bool = False
    ) -> None:
        if not exist_ok:
            try:
                await self.stats(uri)
            except ResourceNotFound:
                pass
            else:
                raise FileExistsError(errno.EEXIST, "File exists", str(uri))

        if not parents:
            parent = uri
            while not parent.name and parent != parent.parent:
                parent = parent.parent
            parent = parent.parent
            if parent != parent.parent:
                try:
                    await self.stats(parent)
                except ResourceNotFound:
                    raise FileNotFoundError(
                        errno.ENOENT, "No such directory", str(parent)
                    )

        url = self._config.cluster_config.storage_url / self._uri_to_path(uri)
        url = url.with_query(op="MKDIRS")

        async with self._core.request("PUT", url) as resp:
            resp  # resp.status == 201

    async def create(self, uri: URL, data: AsyncIterator[bytes]) -> None:
        path = self._uri_to_path(uri)
        assert path, "Creation in root is not allowed"
        url = self._config.cluster_config.storage_url / path
        url = url.with_query(op="CREATE")
        timeout = attr.evolve(self._core.timeout, sock_read=None)

        async with self._core.request("PUT", url, data=data, timeout=timeout) as resp:
            resp  # resp.status == 201

    async def stats(self, uri: URL) -> FileStatus:
        url = self._config.cluster_config.storage_url / self._uri_to_path(uri)
        url = url.with_query(op="GETFILESTATUS")

        async with self._core.request("GET", url) as resp:
            res = await resp.json()
            return FileStatus.from_api(res["FileStatus"])

    async def _is_dir(self, uri: URL) -> bool:
        if uri.scheme == "storage":
            try:
                stat = await self.stats(uri)
                return stat.is_dir()
            except ResourceNotFound:
                pass
        elif uri.scheme == "file":
            path = _extract_path(uri)
            return path.is_dir()
        return False

    async def open(self, uri: URL) -> AsyncIterator[bytes]:
        url = self._config.cluster_config.storage_url / self._uri_to_path(uri)
        url = url.with_query(op="OPEN")
        timeout = attr.evolve(self._core.timeout, sock_read=None)

        async with self._core.request("GET", url, timeout=timeout) as resp:
            async for data in resp.content.iter_any():
                yield data

    async def rm(self, uri: URL, *, recursive: bool = False) -> None:
        path = self._uri_to_path(uri)
        # TODO (asvetlov): add a minor protection against deleting everything from root
        # or user volume root, however force operation here should allow user to delete
        # everything.
        #
        # Now it doesn't make sense because URL for root folder (storage:///) is not
        # supported
        #
        # parts = path.split('/')
        # if final_path == root_data_path or final_path.parent == root_data_path:
        #     raise ValueError("Invalid path value.")

        if not recursive:
            stats = await self.stats(uri)
            if stats.type is FileStatusType.DIRECTORY:
                raise IsADirectoryError(
                    errno.EISDIR, "Is a directory, use recursive remove", str(uri)
                )

        url = self._config.cluster_config.storage_url / path
        url = url.with_query(op="DELETE")

        async with self._core.request("DELETE", url) as resp:
            resp  # resp.status == 204

    async def mv(self, src: URL, dst: URL) -> None:
        url = self._config.cluster_config.storage_url / self._uri_to_path(src)
        url = url.with_query(op="RENAME", destination="/" + self._uri_to_path(dst))

        async with self._core.request("POST", url) as resp:
            resp  # resp.status == 204

    # high-level helpers

    async def _iterate_file(
        self, src: Path, dst: URL, *, progress: Optional[AbstractProgress] = None
    ) -> AsyncIterator[bytes]:
        loop = asyncio.get_event_loop()
        with src.open("rb") as stream:
            if progress is not None:
                progress.start(str(src), str(dst), os.stat(stream.fileno()).st_size)
            chunk = await loop.run_in_executor(None, stream.read, 1024 * 1024)
            pos = len(chunk)
            while chunk:
                if progress is not None:
                    progress.progress(str(src), str(dst), pos)
                yield chunk
                chunk = await loop.run_in_executor(None, stream.read, 1024 * 1024)
                pos += len(chunk)
            if progress is not None:
                progress.complete(str(src), str(dst))

    async def upload_file(
        self, src: URL, dst: URL, *, progress: Optional[AbstractProgress] = None
    ) -> None:
        src = normalize_local_path_uri(src)
        dst = normalize_storage_path_uri(dst, self._config.auth_token.username)
        path = _extract_path(src)
        try:
            if not path.exists():
                raise FileNotFoundError(errno.ENOENT, "No such file", str(path))
            if path.is_dir():
                raise IsADirectoryError(
                    errno.EISDIR, "Is a directory, use recursive copy", str(path)
                )
        except OSError as e:
            if getattr(e, "winerror", None) not in (1, 87):
                raise
            # Ignore stat errors for device files like NUL or CON on Windows.
            # See https://bugs.python.org/issue37074
        try:
            stats = await self.stats(dst)
            if stats.is_dir():
                raise IsADirectoryError(errno.EISDIR, "Is a directory", str(dst))
        except ResourceNotFound:
            # target doesn't exist, lookup for parent dir
            try:
                stats = await self.stats(dst.parent)
                if not stats.is_dir():
                    # parent path should be a folder
                    raise NotADirectoryError(
                        errno.ENOTDIR, "Not a directory", str(dst.parent)
                    )
            except ResourceNotFound:
                raise NotADirectoryError(
                    errno.ENOTDIR, "Not a directory", str(dst.parent)
                )
        await self.create(dst, self._iterate_file(path, dst, progress=progress))

    async def upload_dir(
        self, src: URL, dst: URL, *, progress: Optional[AbstractProgress] = None
    ) -> None:
        src = normalize_local_path_uri(src)
        dst = normalize_storage_path_uri(dst, self._config.auth_token.username)
        path = _extract_path(src).resolve()
        if not path.exists():
            raise FileNotFoundError(errno.ENOENT, "No such file", str(path))
        if not path.is_dir():
            raise NotADirectoryError(errno.ENOTDIR, "Not a directory", str(path))
        try:
            stat = await self.stats(dst)
            if not stat.is_dir():
                raise NotADirectoryError(errno.ENOTDIR, "Not a directory", str(dst))
        except ResourceNotFound:
            await self.mkdirs(dst)
        if progress is not None:
            progress.mkdir(str(path), str(dst))
        for child in path.iterdir():
            if child.is_file():
                await self.upload_file(
                    src / child.name, dst / child.name, progress=progress
                )
            elif child.is_dir():
                await self.upload_dir(
                    src / child.name, dst / child.name, progress=progress
                )
            else:
                # This case is for uploading non-regular file,
                # e.g. blocking device or unix socket
                # Coverage temporary skipped, the line is waiting for a champion
                log.warning("Cannot upload %s", child)  # pragma: no cover

    async def download_file(
        self, src: URL, dst: URL, *, progress: Optional[AbstractProgress] = None
    ) -> None:
        src = normalize_storage_path_uri(src, self._config.auth_token.username)
        dst = normalize_local_path_uri(dst)
        path = _extract_path(dst)
        loop = asyncio.get_event_loop()
        with path.open("wb") as stream:
            stat = await self.stats(src)
            if not stat.is_file():
                raise IsADirectoryError(errno.EISDIR, "Is a directory", str(src))
            size = stat.size
            if progress is not None:
                progress.start(str(src), str(path), size)
            pos = 0
            async for chunk in self.open(src):
                pos += len(chunk)
                if progress is not None:
                    progress.progress(str(src), str(path), pos)
                await loop.run_in_executor(None, stream.write, chunk)
            if progress is not None:
                progress.complete(str(src), str(path))

    async def download_dir(
        self, src: URL, dst: URL, *, progress: Optional[AbstractProgress] = None
    ) -> None:
        src = normalize_storage_path_uri(src, self._config.auth_token.username)
        dst = normalize_local_path_uri(dst)
        path = _extract_path(dst)
        path.mkdir(parents=True, exist_ok=True)
        if progress is not None:
            progress.mkdir(str(src), str(path))
        for child in await self.ls(src):
            if child.is_file():
                await self.download_file(
                    src / child.name, dst / child.name, progress=progress
                )
            elif child.is_dir():
                await self.download_dir(
                    src / child.name, dst / child.name, progress=progress
                )
            else:
                log.warning("Cannot download %s", child)  # pragma: no cover
