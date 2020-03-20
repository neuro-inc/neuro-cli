import asyncio
import base64
import fnmatch
import hashlib
import re
import time
from dataclasses import dataclass
from email.utils import parsedate
from pathlib import Path, PurePath
from typing import Any, AsyncIterator, Dict, List, Optional, Union, cast

import aiohttp
import attr
from dateutil.parser import isoparse
from yarl import URL

from .config import Config
from .core import _Core
from .storage import _has_magic
from .users import Action
from .utils import NoPublicConstructor, asynccontextmanager


MAX_OPEN_FILES = 20
READ_SIZE = 2 ** 20  # 1 MiB


def _format_bucket_uri(bucket_name: str, key: str = "") -> URL:
    return URL.build(scheme="object", host=bucket_name, path="/" + key.lstrip("/"))


@dataclass(frozen=True)
class BucketListing:
    name: str
    modification_time: int
    # XXX: Add real bucket permission access level
    permission: Action = Action.READ

    @property
    def uri(self) -> URL:
        return _format_bucket_uri(self.name, "")


@dataclass(frozen=True)
class ObjectListing:
    key: str
    size: int
    modification_time: int

    @property
    def name(self) -> str:
        return PurePath(self.key).name

    bucket_name: str

    @property
    def uri(self) -> URL:
        return _format_bucket_uri(self.bucket_name, self.key)


@dataclass(frozen=True)
class PrefixListing:
    prefix: str

    @property
    def name(self) -> str:
        return PurePath(self.prefix).name

    bucket_name: str

    @property
    def uri(self) -> URL:
        return _format_bucket_uri(self.bucket_name, self.prefix)


ListResult = Union[PrefixListing, ObjectListing]


class Object:
    def __init__(self, resp: aiohttp.ClientResponse, stats: ObjectListing):
        self._resp = resp
        self.stats = stats

    @property
    def body_stream(self) -> aiohttp.StreamReader:
        return self._resp.content


class ObjectStorage(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: Config) -> None:
        self._core = core
        self._config = config
        self._max_keys = 10000
        self._file_sem = asyncio.BoundedSemaphore(MAX_OPEN_FILES)

    async def list_buckets(self) -> List[BucketListing]:
        url = self._config.object_storage_url / "b" / ""
        auth = await self._config._api_auth()

        async with self._core.request("GET", url, auth=auth) as resp:
            res = await resp.json()
            return [_bucket_status_from_data(bucket) for bucket in res]

    async def list_objects(
        self,
        bucket_name: str,
        prefix: str = "",
        recursive: bool = False,
        max_keys: int = 10000,
    ) -> List[ListResult]:
        url = self._config.object_storage_url / "o" / bucket_name
        auth = await self._config._api_auth()

        query = {"recursive": str(recursive).lower(), "max_keys": str(self._max_keys)}
        if prefix:
            query["prefix"] = prefix
        url = url.with_query(query)

        contents: List[ListResult] = []
        common_prefixes: List[ListResult] = []
        while True:
            async with self._core.request("GET", url, auth=auth) as resp:
                res = await resp.json()
                contents.extend(
                    [_obj_status_from_key(bucket_name, key) for key in res["contents"]]
                )
                common_prefixes.extend(
                    [
                        _obj_status_from_prefix(bucket_name, prefix)
                        for prefix in res["common_prefixes"]
                    ]
                )
                if res["is_truncated"] and res["contents"]:
                    start_after = res["contents"][-1]["key"]
                    url = url.update_query(start_after=start_after)
                else:
                    break
        return common_prefixes + contents

    async def glob_objects(self, bucket_name: str, pattern: str) -> List[ObjectListing]:
        pattern = pattern.lstrip("/")
        parts = pattern.split("/")
        # Limit the search to prefix of keys
        prefix = ""
        for part in parts:
            if _has_magic(part):
                break
            else:
                prefix += part + "/"

        match = re.compile(fnmatch.translate(pattern)).fullmatch
        res = []
        for obj_status in await self.list_objects(
            bucket_name, prefix=prefix, recursive=True
        ):
            # We don't have PrefixListing if recursive is used
            obj_status = cast(ObjectListing, obj_status)
            if match(obj_status.key):
                res.append(obj_status)
        return res

    async def head_object(self, bucket_name: str, key: str) -> ObjectListing:
        url = self._config.object_storage_url / "o" / bucket_name / key
        auth = await self._config._api_auth()

        async with self._core.request("HEAD", url, auth=auth) as resp:
            return _obj_status_from_response(bucket_name, key, resp)

    @asynccontextmanager
    async def get_object(self, bucket_name: str, key: str) -> AsyncIterator[Object]:
        """ Return object status and body stream of the object
        """
        url = self._config.object_storage_url / "o" / bucket_name / key
        auth = await self._config._api_auth()

        timeout = attr.evolve(self._core.timeout, sock_read=None)
        async with self._core.request("GET", url, timeout=timeout, auth=auth) as resp:
            stats = _obj_status_from_response(bucket_name, key, resp)
            yield Object(resp, stats)

    async def fetch_object(self, bucket_name: str, key: str) -> AsyncIterator[bytes]:
        """ Return only bytes data of the object
        """
        async with self.get_object(bucket_name, key) as obj:
            async for data in obj.body_stream.iter_any():
                yield data

    async def put_object(
        self,
        bucket_name: str,
        key: str,
        body_stream: AsyncIterator[bytes],
        size: int,
        content_md5: Optional[str] = None,
    ) -> str:
        url = self._config.object_storage_url / "o" / bucket_name / key
        auth = await self._config._api_auth()
        timeout = attr.evolve(self._core.timeout, sock_read=None)

        # We don't provide Content-Length as transfer endcoding will be `chunked`.
        # But the server needs to know the decoded length of the file.
        headers = {"X-Content-Length": str(size)}
        if content_md5 is not None:
            headers["Content-MD5"] = content_md5

        async with self._core.request(
            "PUT", url, data=body_stream, timeout=timeout, auth=auth, headers=headers
        ) as resp:
            etag = resp.headers["ETag"]
            return etag


def _bucket_status_from_data(data: Dict[str, Any]) -> BucketListing:
    mtime = isoparse(data["creation_date"]).timestamp()
    return BucketListing(name=data["name"], modification_time=int(mtime))


def _obj_status_from_key(bucket_name: str, data: Dict[str, Any]) -> ObjectListing:
    return ObjectListing(
        bucket_name=bucket_name,
        key=data["key"],
        size=int(data["size"]),
        modification_time=int(data["last_modified"]),
    )


def _obj_status_from_prefix(bucket_name: str, data: Dict[str, Any]) -> PrefixListing:
    return PrefixListing(bucket_name=bucket_name, prefix=data["prefix"])


def _obj_status_from_response(
    bucket_name: str, key: str, resp: aiohttp.ClientResponse
) -> ObjectListing:
    modification_time = 0
    if "Last-Modified" in resp.headers:
        timetuple = parsedate(resp.headers["Last-Modified"])
        if timetuple is not None:
            modification_time = int(time.mktime(timetuple))
    return ObjectListing(
        bucket_name=bucket_name,
        key=key,
        size=resp.content_length or 0,
        modification_time=modification_time,
    )


async def calc_md5(path: Path) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _calc_md5_blocking, path)


def _calc_md5_blocking(path: Path) -> str:
    md5 = hashlib.md5()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(READ_SIZE)
            if not chunk:
                break
            md5.update(chunk)
    return base64.b64encode(md5.digest()).decode("ascii")
