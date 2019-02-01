import asyncio
import enum
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List

from yarl import URL

from neuromation.client.url_utils import (
    normalize_local_path_uri,
    normalize_storage_path_uri,
)

from .abc import AbstractProgress
from .api import API, ResourceNotFound
from .config import Config


log = logging.getLogger(__name__)


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
            type=values["type"],
            size=int(values["length"]),
            modification_time=int(values["modificationTime"]),
            permission=values["permission"],
        )


class Storage:
    def __init__(self, api: API, config: Config) -> None:
        self._api = api
        self._config = config

    def _uri_to_path(self, uri: URL) -> str:
        uri = normalize_storage_path_uri(uri, self._config.username)
        prefix = uri.host + "/" if uri.host else ""
        return prefix + uri.path.lstrip("/")

    async def ls(self, uri: URL) -> List[FileStatus]:
        url = URL("storage") / self._uri_to_path(uri)
        url = url.with_query(op="LISTSTATUS")

        async with self._api.request("GET", url) as resp:
            res = await resp.json()
            return [
                FileStatus.from_api(status)
                for status in res["FileStatuses"]["FileStatus"]
            ]

    async def mkdirs(self, uri: URL) -> None:
        url = URL("storage") / self._uri_to_path(uri)
        url = url.with_query(op="MKDIRS")

        async with self._api.request("PUT", url) as resp:
            resp  # resp.status == 201

    async def create(self, uri: URL, data: AsyncIterator[bytes]) -> None:
        path = self._uri_to_path(uri)
        assert path, "Creation in root is not allowed"
        url = URL("storage") / path
        url = url.with_query(op="CREATE")

        async with self._api.request("PUT", url, data=data) as resp:
            resp  # resp.status == 201

    async def stats(self, uri: URL) -> FileStatus:
        url = URL("storage") / self._uri_to_path(uri)
        url = url.with_query(op="GETFILESTATUS")

        async with self._api.request("GET", url) as resp:
            res = await resp.json()
            return FileStatus.from_api(res["FileStatus"])

    async def open(self, uri: URL) -> AsyncIterator[bytes]:
        stat = await self.stats(uri)
        if not stat.is_file():
            raise IsADirectoryError(uri)
        url = URL("storage") / self._uri_to_path(uri)
        url = url.with_query(op="OPEN")

        async with self._api.request("GET", url) as resp:
            async for data in resp.content.iter_any():
                yield data

    async def rm(self, uri: URL) -> None:
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

        url = URL("storage") / path
        url = url.with_query(op="DELETE")

        async with self._api.request("DELETE", url) as resp:
            resp  # resp.status == 204

    async def mv(self, src: URL, dst: URL) -> None:
        url = URL("storage") / self._uri_to_path(src)
        url = url.with_query(op="RENAME", destination="/" + self._uri_to_path(dst))

        async with self._api.request("POST", url) as resp:
            resp  # resp.status == 204

    # high-level helpers

    async def _iterate_file(
        self, progress: AbstractProgress, src: Path
    ) -> AsyncIterator[bytes]:
        loop = asyncio.get_event_loop()
        progress.start(str(src), src.stat().st_size)
        with src.open("rb") as stream:
            chunk = await loop.run_in_executor(None, stream.read, 1024 * 1024)
            pos = len(chunk)
            while chunk:
                progress.progress(str(src), pos)
                yield chunk
                chunk = await loop.run_in_executor(None, stream.read, 1024 * 1024)
                pos += len(chunk)
            progress.complete(str(src))

    async def upload_file(self, progress: AbstractProgress, src: URL, dst: URL) -> None:
        src = normalize_local_path_uri(src)
        dst = normalize_storage_path_uri(dst, self._config.username)
        path = Path(src.path)
        if not path.exists():
            raise FileNotFoundError(f"'{path}' does not exist")
        if path.is_dir():
            raise IsADirectoryError(f"'{path}' is a directory, use recursive copy")
        if not path.is_file():
            raise OSError(f"'{path}' should be a regular file")
        if not dst.name:
            # file:src/file.txt -> storage:dst/ ==> storage:dst/file.txt
            dst = dst / src.name
        try:
            stats = await self.stats(dst)
            if stats.is_dir():
                # target exists and it is a folder
                dst = dst / src.name
        except ResourceNotFound:
            # target doesn't exist, lookup for parent dir
            try:
                stats = await self.stats(dst.parent)
                if not stats.is_dir():
                    # parent path should be a folder
                    raise NotADirectoryError(dst.parent)
            except ResourceNotFound:
                raise NotADirectoryError(dst.parent)
        await self.create(dst, self._iterate_file(progress, path))

    async def upload_dir(self, progress: AbstractProgress, src: URL, dst: URL) -> None:
        if not dst.name:
            # /dst/ ==> /dst for recursive copy
            dst = dst / src.name
        src = normalize_local_path_uri(src)
        dst = normalize_storage_path_uri(dst, self._config.username)
        path = Path(src.path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"{path} does not exist")
        if not path.is_dir():
            raise NotADirectoryError(f"{path} should be a directory")
        try:
            stat = await self.stats(dst)
            if not stat.is_dir():
                raise NotADirectoryError(f"{dst} should be a directory")
        except ResourceNotFound:
            await self.mkdirs(dst)
        for child in path.iterdir():
            if child.is_file():
                await self.upload_file(progress, src / child.name, dst / child.name)
            elif child.is_dir():
                await self.upload_dir(progress, src / child.name, dst / child.name)
            else:
                # This case is for uploading non-regular file,
                # e.g. blocking device or unix socket
                # Coverage temporary skipped, the line is waiting for a champion
                log.warning("Cannot upload %s", child)  # pragma: no cover

    async def download_file(
        self, progress: AbstractProgress, src: URL, dst: URL
    ) -> None:
        src = normalize_storage_path_uri(src, self._config.username)
        dst = normalize_local_path_uri(dst)
        path = Path(dst.path)
        if path.exists():
            if path.is_dir():
                path = path / src.name
            elif not path.is_file():
                raise OSError(f"{path} should be a regular file")
        loop = asyncio.get_event_loop()
        with path.open("wb") as stream:
            size = 0  # TODO: display length hint for downloaded file
            progress.start(str(dst), size)
            pos = 0
            async for chunk in self.open(src):
                pos += len(chunk)
                progress.progress(str(dst), pos)
                await loop.run_in_executor(None, stream.write, chunk)
            progress.complete(str(dst))

    async def download_dir(
        self, progress: AbstractProgress, src: URL, dst: URL
    ) -> None:
        src = normalize_storage_path_uri(src, self._config.username)
        dst = normalize_local_path_uri(dst)
        path = Path(dst.path)
        path.mkdir(parents=True, exist_ok=True)
        for child in await self.ls(src):
            if child.is_file():
                await self.download_file(progress, src / child.name, dst / child.name)
            elif child.is_dir():
                await self.download_dir(progress, src / child.name, dst / child.name)
            else:
                log.warning("Cannot download %s", child)  # pragma: no cover
