import enum
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List

from yarl import URL

from .api import API


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

    def is_file(self):
        return self.type == FileStatusType.FILE

    def is_dir(self):
        return self.type == FileStatusType.DIRECTORY

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
    def __init__(self, api: API, username: str) -> None:
        self._api = api
        self._username = username

    def _uri_to_path(self, uri: URL) -> str:
        if uri.scheme != "storage":
            # TODO (asvetlov): change error text, mention storage:// prefix explicitly
            raise ValueError("Path should be targeting platform storage.")

        ret: List[str] = []
        if uri.host == "~":
            ret.append(self._username)
        elif not uri.is_absolute():
            # absolute paths are considered as relative to home dir
            ret.append(self._username)
        else:
            assert uri.host
            ret.append(uri.host)
        path = uri.path.strip("/")
        if path:
            ret.extend(path.split("/"))
        return "/".join(ret)

    def normalize(self, uri: URL) -> URL:
        if uri.scheme != "storage":
            # TODO (asvetlov): change error text, mention storage:// prefix explicitly
            raise ValueError("Path should be targeting platform storage.")

        if uri.host == "~":
            uri = uri.with_host(self._username)
        return uri

    def normalize_local(self, uri: URL) -> URL:
        if uri.scheme != "file":
            # TODO (asvetlov): change error text, mention storage:// prefix explicitly
            raise ValueError("Path should be targeting local file system.")
        if uri.host:
            raise ValueError("Host part is not allowed")
        path = Path(uri.path)
        path = path.expanduser()
        path = path.resolve()
        return uri.with_path(str(path))

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

    async def open(self, *, uri: URL) -> AsyncIterator[bytes]:
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
