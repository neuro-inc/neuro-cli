import asyncio
import enum
import errno
import fnmatch
import itertools
import os
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple

import aiohttp
import attr
from aiohttp import ClientWebSocketResponse, WSCloseCode
from yarl import URL

import cbor

from .abc import (
    AbstractFileProgress,
    AbstractRecursiveFileProgress,
    StorageProgressComplete,
    StorageProgressEnterDir,
    StorageProgressFail,
    StorageProgressLeaveDir,
    StorageProgressStart,
    StorageProgressStep,
)
from .config import _Config
from .core import ResourceNotFound, _Core
from .url_utils import (
    _extract_path,
    normalize_local_path_uri,
    normalize_storage_path_uri,
)
from .utils import NoPublicConstructor, asynccontextmanager


WS_READ_SIZE = 2 ** 20  # 1 MiB
MAX_WS_READ_SIZE = 16 * 2 ** 20  # 16 MiB
MAX_WS_MESSAGE_SIZE = MAX_WS_READ_SIZE + 2 ** 16 + 100

Printer = Callable[[str], None]


class FileStatusType(str, enum.Enum):
    DIRECTORY = "DIRECTORY"
    FILE = "FILE"


class WSStorageOperation(str, enum.Enum):
    ACK = "ACK"
    ERROR = "ERROR"
    READ = "READ"
    STAT = "STAT"
    LIST = "LIST"
    CREATE = "CREATE"
    WRITE = "WRITE"
    MKDIRS = "MKDIRS"


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


class WSStorageClient:
    def __init__(self, ws: ClientWebSocketResponse, idgen: Callable[[], int]) -> None:
        self._client = ws
        self._new_req_id = idgen

    async def send(
        self,
        op: WSStorageOperation,
        path: str = "",
        params: Dict[str, Any] = {},
        data: bytes = b"",
    ) -> int:
        reqid = self._new_req_id()
        payload = {"op": op.value, "id": reqid, "path": path, **params}
        header = cbor.dumps(payload)
        await self._client.send_bytes(
            struct.pack("!I", len(header) + 4) + header + data
        )
        return reqid

    async def receive(self) -> Tuple[Dict[str, Any], bytes]:
        msg = await self._client.receive()
        if msg.type == aiohttp.WSMsgType.BINARY:
            return await self._unpack(msg.data)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            raise msg.data
        else:
            raise RuntimeError("Unsupported WebSocket message type {msg.type}")

    async def _unpack(self, resp: bytes) -> Tuple[Dict[str, Any], bytes]:
        if len(resp) < 4:
            await self._client.close(code=WSCloseCode.UNSUPPORTED_DATA)
            raise RuntimeError("Too short message")
        if len(resp) > MAX_WS_MESSAGE_SIZE:
            await self._client.close(code=WSCloseCode.MESSAGE_TOO_BIG)
            raise RuntimeError("Too large message")
        hsize, = struct.unpack("!I", resp[:4])
        payload = cbor.loads(resp[4:hsize])
        op = payload["op"]
        if op == WSStorageOperation.ACK:
            return payload, resp[hsize:]

        if op == WSStorageOperation.ERROR:
            if "errno" in payload:
                raise OSError(payload["errno"], payload["error"])
            raise RuntimeError(payload["error"])

        raise RuntimeError(f"Unexpected response {payload!r}")

    async def send_checked(
        self,
        op: WSStorageOperation,
        path: str = "",
        params: Dict[str, Any] = {},
        data: bytes = b"",
    ) -> Tuple[Dict[str, Any], bytes]:
        reqid = await self.send(op, path, params, data)
        payload, data = await self.receive()
        rop = payload["rop"]
        respid = payload["respid"]
        if respid != reqid:
            raise RuntimeError(
                f"Unexpected response id {respid} for operation {op}, expected {reqid}"
            )
        if rop != op:
            raise RuntimeError(
                f"Unexpected response op {rop} for request #{reqid}, expected {op}"
            )
        return payload, data


class Storage(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: _Config) -> None:
        self._core = core
        self._config = config
        self._req_id_seq = itertools.count()

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
                _file_status_from_api(status)
                for status in res["FileStatuses"]["FileStatus"]
            ]

    async def glob(self, uri: URL, *, dironly: bool = False) -> AsyncIterator[URL]:
        if not _has_magic(uri.path):
            yield uri
            return
        basename = uri.name
        glob_in_dir: Callable[[URL, str, bool], AsyncIterator[URL]]
        if not _has_magic(basename):
            glob_in_dir = self._glob0
        elif not _isrecursive(basename):
            glob_in_dir = self._glob1
        else:
            glob_in_dir = self._glob2
        async for parent in self.glob(uri.parent, dironly=True):
            async for x in glob_in_dir(parent, basename, dironly):
                yield x

    async def _glob2(
        self, parent: URL, pattern: str, dironly: bool
    ) -> AsyncIterator[URL]:
        assert _isrecursive(pattern)
        yield parent
        async for x in self._rlistdir(parent, dironly):
            yield x

    async def _glob1(
        self, parent: URL, pattern: str, dironly: bool
    ) -> AsyncIterator[URL]:
        allow_hidden = _ishidden(pattern)
        match = re.compile(fnmatch.translate(pattern)).fullmatch
        async for stat in self._iterdir(parent, dironly):
            name = stat.path
            if (allow_hidden or not _ishidden(name)) and match(name):
                yield parent / name

    async def _glob0(
        self, parent: URL, basename: str, dironly: bool
    ) -> AsyncIterator[URL]:
        uri = parent / basename
        try:
            await self.stats(uri)
        except ResourceNotFound:
            return
        yield uri

    async def _iterdir(self, uri: URL, dironly: bool) -> AsyncIterator[FileStatus]:
        for stat in await self.ls(uri):
            if not dironly or stat.is_dir():
                yield stat

    async def _rlistdir(self, uri: URL, dironly: bool) -> AsyncIterator[URL]:
        async for stat in self._iterdir(uri, dironly):
            name = stat.path
            if not _ishidden(name):
                x = uri / name
                yield x
                if stat.is_dir():
                    async for y in self._rlistdir(x, dironly):
                        yield y

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
            return _file_status_from_api(res["FileStatus"])

    async def _stat(self, ws: WSStorageClient, path: str) -> FileStatus:
        payload, data = await ws.send_checked(WSStorageOperation.STAT, path)
        return _file_status_from_api(payload["FileStatus"])

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

    async def upload_file(
        self, src: URL, dst: URL, *, progress: Optional[AbstractFileProgress] = None
    ) -> None:
        if progress is None:
            progress = _DummyProgress()
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

        async with self._ws_connect(dst, "WEBSOCKET_WRITE") as ws:
            await self._upload_file(ws, src, path, dst, "", progress=progress)

    # XXX Move to WSStorageClient?
    async def _upload_file(
        self,
        ws: WSStorageClient,
        src: URL,
        src_path: Path,
        dst: URL,
        dst_path: str = "",
        *,
        progress: AbstractFileProgress,
    ) -> None:
        loop = asyncio.get_event_loop()
        with src_path.open("rb") as stream:
            size = os.stat(stream.fileno()).st_size
            progress.start(StorageProgressStart(src, dst, size))
            await ws.send_checked(WSStorageOperation.CREATE, dst_path, {"size": size})
            pos = 0
            while True:
                chunk = await loop.run_in_executor(None, stream.read, WS_READ_SIZE)
                if not chunk:
                    break
                newpos = pos + len(chunk)
                progress.step(StorageProgressStep(src, dst, pos, size))
                await ws.send_checked(
                    WSStorageOperation.WRITE, dst_path, {"offset": pos}, data=chunk
                )
                pos = newpos
            progress.complete(StorageProgressComplete(src, dst, size))

    async def upload_dir(
        self,
        src: URL,
        dst: URL,
        *,
        progress: Optional[AbstractRecursiveFileProgress] = None,
    ) -> None:
        if progress is None:
            progress = _DummyProgress()
        src = normalize_local_path_uri(src)
        dst = normalize_storage_path_uri(dst, self._config.auth_token.username)
        path = _extract_path(src).resolve()
        if not path.exists():
            raise FileNotFoundError(errno.ENOENT, "No such file", str(path))
        if not path.is_dir():
            raise NotADirectoryError(errno.ENOTDIR, "Not a directory", str(path))

        async with self._ws_connect(dst, "WEBSOCKET_WRITE") as ws:
            await self._upload_dir(ws, src, path, dst, "", progress=progress)

    async def _upload_dir(
        self,
        ws: WSStorageClient,
        src_uri: URL,
        src_path: Path,
        dst_uri: URL,
        dst_path: str = "",
        *,
        progress: AbstractRecursiveFileProgress,
    ) -> None:
        progress.enter(StorageProgressEnterDir(src_uri, dst_uri))
        folder = sorted(src_path.iterdir(), key=lambda item: (item.is_dir(), item.name))
        await ws.send_checked(WSStorageOperation.MKDIRS, dst_path)
        for child in folder:
            name = child.name
            if child.is_file():
                await self._upload_file(
                    ws,
                    src_uri / name,
                    src_path / name,
                    dst_uri / name,
                    f"{dst_path}/{name}",
                    progress=progress,
                )
            elif child.is_dir():
                await self._upload_dir(
                    ws,
                    src_uri / name,
                    src_path / name,
                    dst_uri / name,
                    f"{dst_path}/{name}",
                    progress=progress,
                )
            else:
                # This case is for uploading non-regular file,
                # e.g. blocking device or unix socket
                # Coverage temporary skipped, the line is waiting for a champion
                progress.fail(
                    StorageProgressFail(
                        src_uri / name,
                        dst_uri / name,
                        f"Cannot upload {child}, not regular file/directory",
                    )
                )  # pragma: no cover
        progress.leave(StorageProgressLeaveDir(src_uri, dst_uri))

    async def download_file(
        self, src: URL, dst: URL, *, progress: Optional[AbstractFileProgress] = None
    ) -> None:
        if progress is None:
            progress = _DummyProgress()
        src = normalize_storage_path_uri(src, self._config.auth_token.username)
        dst = normalize_local_path_uri(dst)
        path = _extract_path(dst)

        async with self._ws_connect(src, "WEBSOCKET_READ") as ws:
            stat = await self._stat(ws, "")
            if not stat.is_file():
                raise IsADirectoryError(errno.EISDIR, "Is a directory", str(src))
            await self._download_file(
                ws, src, "", dst, path, stat.size, progress=progress
            )

    async def _download_file(
        self,
        ws: WSStorageClient,
        src: URL,
        src_path: str,
        dst: URL,
        dst_path: Path,
        size: int,
        *,
        progress: AbstractFileProgress,
    ) -> None:
        loop = asyncio.get_event_loop()
        with dst_path.open("wb") as stream:
            progress.start(StorageProgressStart(src, dst, size))
            pos = 0
            while pos < size:
                payload, data = await ws.send_checked(
                    WSStorageOperation.READ,
                    src_path,
                    {"offset": pos, "size": min(WS_READ_SIZE, size - pos)},
                )
                pos += len(data)
                progress.step(StorageProgressStep(src, dst, pos, size))
                await loop.run_in_executor(None, stream.write, data)
            progress.complete(StorageProgressComplete(src, dst, size))

    async def download_dir(
        self,
        src: URL,
        dst: URL,
        *,
        progress: Optional[AbstractRecursiveFileProgress] = None,
    ) -> None:
        if progress is None:
            progress = _DummyProgress()
        src = normalize_storage_path_uri(src, self._config.auth_token.username)
        dst = normalize_local_path_uri(dst)
        path = _extract_path(dst)

        async with self._ws_connect(src, "WEBSOCKET_READ") as ws:
            await self._download_dir(ws, src, "", dst, path, progress=progress)

    async def _download_dir(
        self,
        ws: WSStorageClient,
        src: URL,
        src_path: str,
        dst: URL,
        dst_path: Path,
        *,
        progress: AbstractRecursiveFileProgress,
    ) -> None:
        progress.enter(StorageProgressEnterDir(src, dst))
        payload, data = await ws.send_checked(WSStorageOperation.LIST, src_path)
        folder = [
            _file_status_from_api(status)
            for status in payload["FileStatuses"]["FileStatus"]
        ]
        folder.sort(key=lambda item: (item.is_dir(), item.path))
        dst_path.mkdir(parents=True, exist_ok=True)
        for child in folder:
            name = child.name
            if child.is_file():
                await self._download_file(
                    ws,
                    src / name,
                    f"{src_path}/{name}",
                    dst / name,
                    dst_path / name,
                    child.size,
                    progress=progress,
                )
            elif child.is_dir():
                await self._download_dir(
                    ws,
                    src / name,
                    f"{src_path}/{name}",
                    dst / name,
                    dst_path / name,
                    progress=progress,
                )
            else:
                progress.fail(
                    StorageProgressFail(
                        src / name,
                        dst / name,
                        f"Cannot download {child}, not regular file/directory",
                    )
                )  # pragma: no cover
        progress.leave(StorageProgressLeaveDir(src, dst))

    def _new_req_id(self) -> int:
        return next(self._req_id_seq)

    @asynccontextmanager
    async def _ws_connect(self, uri: URL, op: str) -> AsyncIterator[WSStorageClient]:
        path = self._uri_to_path(uri)
        assert op == "WEBSOCKET_READ" or path, "Creation in root is not allowed"
        url = self._config.cluster_config.storage_url / path
        url = url.with_query(op=op)
        async with self._core._session.ws_connect(url) as ws:
            yield WSStorageClient(ws, self._new_req_id)


_magic_check = re.compile("(?:[*?[])")


def _has_magic(s: str) -> bool:
    return _magic_check.search(s) is not None


def _ishidden(name: str) -> bool:
    return name.startswith(".")


def _isrecursive(pattern: str) -> bool:
    return pattern == "**"


def _file_status_from_api(values: Dict[str, Any]) -> FileStatus:
    return FileStatus(
        path=values["path"],
        type=FileStatusType(values["type"]),
        size=int(values["length"]),
        modification_time=int(values["modificationTime"]),
        permission=values["permission"],
    )


class _DummyProgress(AbstractRecursiveFileProgress):
    def start(self, data: StorageProgressStart) -> None:
        pass

    def complete(self, data: StorageProgressComplete) -> None:
        pass

    def step(self, data: StorageProgressStep) -> None:
        pass

    def enter(self, data: StorageProgressEnterDir) -> None:
        pass

    def leave(self, data: StorageProgressLeaveDir) -> None:
        pass

    def fail(self, data: StorageProgressFail) -> None:
        pass
