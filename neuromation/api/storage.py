import asyncio
import enum
import errno
import fnmatch
import itertools
import logging
import os
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    AsyncGenerator,
    AsyncIterator,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

import aiohttp
import attr
import cbor
from aiohttp import ClientWebSocketResponse, WSCloseCode
from yarl import URL

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


log = logging.getLogger(__name__)

WS_READ_SIZE = 2 ** 20  # 1 MiB
MAX_WS_READ_SIZE = 16 * 2 ** 20  # 16 MiB
MAX_WS_MESSAGE_SIZE = MAX_WS_READ_SIZE + 2 ** 16 + 100

Printer = Callable[[str], None]
WSStorageHandler = AsyncGenerator[None, Tuple[Dict[str, Any], bytes]]


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
    def __init__(
        self, ws: ClientWebSocketResponse, root: URL, idgen: Callable[[], int]
    ) -> None:
        self._client = ws
        self._root = root
        self._new_req_id = idgen
        self._handlers: Dict[int, WSStorageHandler] = {}

    async def async_request(
        self,
        op: WSStorageOperation,
        path: str = "",
        params: Dict[str, Any] = {},
        data: bytes = b"",
        *,
        handler: WSStorageHandler,
    ) -> None:
        reqid = self._new_req_id()
        payload = {"op": op.value, "id": reqid, "path": path, **params}
        if data:
            log.debug("WS send: %s, %d bytes", payload, len(data))
        else:
            log.debug("WS send: %s", payload)
        header = cbor.dumps(payload)
        await handler.__anext__()
        self._handlers[reqid] = handler
        await self._client.send_bytes(
            struct.pack("!I", len(header) + 4) + header + data
        )

    async def parse_msg(
        self, resp: bytes
    ) -> Tuple[Dict[str, Any], Union[bytes, BaseException]]:
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
            data = resp[hsize:]
            if data:
                log.debug("WS receive: %s, %d bytes", payload, len(data))
            else:
                log.debug("WS receive: %s", payload)
            return payload, data

        if op == WSStorageOperation.ERROR:
            exc: BaseException
            if "errno" in payload:
                exc = OSError(
                    errno.__dict__.get(payload["errno"], payload["errno"]),
                    payload["error"],
                )
            else:
                exc = RuntimeError(payload["error"])
            log.debug("WS error: %s", payload)
            return payload, exc

        raise RuntimeError(f"Unexpected response {payload!r}")

    async def run(self) -> None:
        async for msg in self._client:
            if msg.type == aiohttp.WSMsgType.BINARY:
                payload, data = await self.parse_msg(msg.data)
                rid = payload["rid"]
                handler = self._handlers.pop(rid)
                try:
                    if isinstance(data, BaseException):
                        await handler.athrow(data)  # type: ignore
                    else:
                        await handler.asend((payload, data))
                except StopAsyncIteration:
                    pass
                else:
                    raise RuntimeError("generator didn't stop")
                if not self._handlers:
                    break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                raise msg.data
            else:
                raise RuntimeError(f"Unsupported WebSocket message type: {msg.type}")

    async def upload_file(
        self, src: Path, dst: str, size: int, *, progress: AbstractFileProgress
    ) -> None:
        src_uri = URL(src.as_uri())
        dst_uri = self._root / dst

        async def create_handler() -> WSStorageHandler:
            payload, data = yield
            progress.start(StorageProgressStart(src_uri, dst_uri, size))
            loop = asyncio.get_event_loop()
            with src.open("rb") as stream:
                pos = 0
                while True:
                    chunk = await loop.run_in_executor(None, stream.read, WS_READ_SIZE)
                    if not chunk:
                        break
                    newpos = pos + len(chunk)
                    progress.step(StorageProgressStep(src_uri, dst_uri, newpos, size))

                    async def write_handler() -> WSStorageHandler:
                        yield

                    await self.async_request(
                        WSStorageOperation.WRITE,
                        dst,
                        {"offset": pos},
                        data=chunk,
                        handler=write_handler(),
                    )
                    pos = newpos
                progress.complete(StorageProgressComplete(src_uri, dst_uri, size))

        await self.async_request(
            WSStorageOperation.CREATE, dst, {"size": size}, handler=create_handler()
        )

    async def upload_dir(
        self, src: Path, dst: str, *, progress: AbstractRecursiveFileProgress
    ) -> None:
        src_uri = URL(src.as_uri())
        dst_uri = self._root / dst

        async def mkdir_handler() -> WSStorageHandler:
            try:
                payload, data = yield
            except FileExistsError:
                raise NotADirectoryError(errno.ENOTDIR, "Not a directory", str(dst_uri))
            progress.enter(StorageProgressEnterDir(src_uri, dst_uri))
            with os.scandir(src) as it:
                folder = sorted(it, key=lambda item: (item.is_dir(), item.name))
            for child in folder:
                name = child.name
                if child.is_file():
                    size = child.stat().st_size
                    await self.upload_file(
                        src / name, _join_path(dst, name), size, progress=progress
                    )
                elif child.is_dir():
                    await self.upload_dir(
                        src / name, _join_path(dst, name), progress=progress
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

        await self.async_request(
            WSStorageOperation.MKDIRS,
            dst,
            {"parents": True, "exist_ok": True},
            handler=mkdir_handler(),
        )

    async def download_file(
        self, src: str, dst: Path, size: int, *, progress: AbstractFileProgress
    ) -> None:
        src_uri = self._root / src if src else self._root
        dst_uri = URL(dst.as_uri())
        loop = asyncio.get_event_loop()

        async def read_handler(
            file_path: Path, offset: int, size: int
        ) -> WSStorageHandler:
            payload, data = yield
            with open(file_path, "rb+", buffering=0) as f:
                f.seek(offset)
                await loop.run_in_executor(None, f.write, data)

        with open(dst, "wb", buffering=0):
            pass
        progress.start(StorageProgressStart(src_uri, dst_uri, size))
        for pos in range(0, size, WS_READ_SIZE):
            chunk_size = min(WS_READ_SIZE, size - pos)
            await self.async_request(
                WSStorageOperation.READ,
                src,
                {"offset": pos, "size": chunk_size},
                handler=read_handler(dst, pos, chunk_size),
            )
            progress.step(StorageProgressStep(src_uri, dst_uri, pos + chunk_size, size))
        progress.complete(StorageProgressComplete(src_uri, dst_uri, size))

    async def download_dir(
        self, src: str, dst: Path, *, progress: AbstractRecursiveFileProgress
    ) -> None:
        src_uri = self._root / src if src else self._root
        dst_uri = URL(dst.as_uri())

        async def list_handler() -> WSStorageHandler:
            payload, data = yield
            progress.enter(StorageProgressEnterDir(src_uri, dst_uri))
            folder = [
                _file_status_from_api(status)
                for status in payload["FileStatuses"]["FileStatus"]
            ]
            folder.sort(key=lambda item: (item.is_dir(), item.path))
            dst.mkdir(parents=True, exist_ok=True)
            for child in folder:
                name = child.name
                if child.is_file():
                    await self.download_file(
                        _join_path(src, name), dst / name, child.size, progress=progress
                    )
                elif child.is_dir():
                    await self.download_dir(
                        _join_path(src, name), dst / name, progress=progress
                    )
                else:
                    assert progress is not None
                    progress.fail(
                        StorageProgressFail(
                            src_uri / name,
                            dst_uri / name,
                            f"Cannot download {child}, not regular file/directory",
                        )
                    )  # pragma: no cover
            progress.leave(StorageProgressLeaveDir(src_uri, dst_uri))

        await self.async_request(WSStorageOperation.LIST, src, handler=list_handler())


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
            size = path.stat().st_size
        except OSError as e:
            if getattr(e, "winerror", None) not in (1, 87):
                raise
            # Ignore stat errors for device files like NUL or CON on Windows.
            # See https://bugs.python.org/issue37074
            size = 0

        async with self._ws_connect(dst.parent, "WEBSOCKET_WRITE") as ws:

            async def stat_handler() -> WSStorageHandler:
                try:
                    payload, data = yield
                except FileNotFoundError:
                    # target's parent doesn't exist
                    raise NotADirectoryError(
                        errno.ENOTDIR, "Not a directory", str(dst.parent)
                    )
                stat = _file_status_from_api(payload["FileStatus"])
                if not stat.is_dir():
                    # parent path should be a folder
                    raise NotADirectoryError(
                        errno.ENOTDIR, "Not a directory", str(dst.parent)
                    )
                assert progress
                await ws.upload_file(path, dst.name, size, progress=progress)

            await ws.async_request(WSStorageOperation.STAT, "", handler=stat_handler())
            await ws.run()

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
            await ws.upload_dir(path, "", progress=progress)
            await ws.run()

    async def download_file(
        self, src: URL, dst: URL, *, progress: Optional[AbstractFileProgress] = None
    ) -> None:
        if progress is None:
            progress = _DummyProgress()
        src = normalize_storage_path_uri(src, self._config.auth_token.username)
        dst = normalize_local_path_uri(dst)
        path = _extract_path(dst)

        async with self._ws_connect(src, "WEBSOCKET_READ") as ws:

            async def stat_handler() -> WSStorageHandler:
                payload, data = yield
                stat = _file_status_from_api(payload["FileStatus"])
                if not stat.is_file():
                    raise IsADirectoryError(errno.EISDIR, "Is a directory", str(src))
                assert progress
                await ws.download_file("", path, stat.size, progress=progress)

            await ws.async_request(WSStorageOperation.STAT, "", handler=stat_handler())
            await ws.run()

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
            await ws.download_dir("", path, progress=progress)
            await ws.run()

    def _new_req_id(self) -> int:
        return next(self._req_id_seq)

    @asynccontextmanager
    async def _ws_connect(self, uri: URL, op: str) -> AsyncIterator[WSStorageClient]:
        path = self._uri_to_path(uri)
        assert op == "WEBSOCKET_READ" or path, "Creation in root is not allowed"
        url = self._config.cluster_config.storage_url / path
        url = url.with_query(op=op)
        async with self._core._session.ws_connect(url) as ws:
            yield WSStorageClient(ws, uri, self._new_req_id)


_magic_check = re.compile("(?:[*?[])")


def _has_magic(s: str) -> bool:
    return _magic_check.search(s) is not None


def _ishidden(name: str) -> bool:
    return name.startswith(".")


def _isrecursive(pattern: str) -> bool:
    return pattern == "**"


def _join_path(basedir: str, name: str) -> str:
    if basedir and name:
        return f"{basedir}/{name}"
    return basedir or name


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
