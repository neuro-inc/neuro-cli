import enum
from dataclasses import dataclass
from typing import Any, BinaryIO, Dict, Iterator, List

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
    def __init__(self, api: API) -> None:
        self._api = api

    async def ls(self, *, path: str) -> List[FileStatus]:
        url = URL("storage") / path.strip("/")
        url = url.with_query(op="LISTSTATUS")

        async with self._api.request("GET", url) as resp:
            res = await resp.json()
            return [
                FileStatus.from_api(status)
                for status in res["FileStatuses"]["FileStatus"]
            ]

    async def mkdirs(self, *, path: str) -> None:
        url = URL("storage") / path.strip("/")
        url = url.with_query(op="MKDIRS")

        async with self._api.request("PUT", url) as resp:
            resp  # resp.status == 201

    async def create(self, *, path: str, data: BinaryIO) -> None:
        url = URL("storage") / path.strip("/")
        url = url.with_query(op="CREATE")

        async with self._api.request("PUT", url, data=data) as resp:
            resp  # resp.status == 201

    async def stats(self, *, path: str) -> FileStatus:
        url = URL("storage") / path.strip("/")
        url = url.with_query(op="GETFILESTATUS")

        async with self._api.request("GET", url) as resp:
            res = await resp.json()
            return FileStatus.from_api(res["FileStatus"])

    async def open(self, *, path: str) -> Iterator[bytes]:
        url = URL("storage") / path.strip("/")
        url = url.with_query(op="OPEN")
        async with self._api.request("GET", url) as resp:
            async for data in resp.content.iter_any():
                yield data

    async def rm(self, *, path: str) -> None:
        url = URL("storage") / path.strip("/")
        url = url.with_query(op="DELETE")

        async with self._api.request("DELETE", url) as resp:
            resp  # resp.status == 204

    async def mv(self, *, src_path: str, dst_path: str) -> None:
        url = URL("storage") / src_path.strip("/")
        url = url.with_query(op="RENAME", destination=dst_path.strip("/"))

        async with self._api.request("POST", url) as resp:
            resp  # resp.status == 204
