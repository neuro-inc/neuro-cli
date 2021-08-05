import abc
import asyncio
import enum
import errno
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from stat import S_ISREG
from typing import AbstractSet, Any, AsyncIterator, Awaitable, Mapping, Optional, Union

import aiobotocore as aiobotocore
import botocore.exceptions
from aiobotocore.client import AioBaseClient
from dateutil.parser import isoparse
from yarl import URL

from neuro_sdk import AbstractRecursiveFileProgress
from neuro_sdk.abc import (
    AbstractFileProgress,
    StorageProgressComplete,
    StorageProgressEnterDir,
    StorageProgressFail,
    StorageProgressLeaveDir,
    StorageProgressStart,
    StorageProgressStep,
    _AsyncAbstractFileProgress,
    _AsyncAbstractRecursiveFileProgress,
)
from neuro_sdk.file_filter import (
    AsyncFilterFunc,
    FileFilter,
    _glob_safe_prefix,
    _has_magic,
    _isrecursive,
    translate,
)
from neuro_sdk.storage import (
    TIME_THRESHOLD,
    _always,
    load_parent_ignore_files,
    run_concurrently,
    run_progress,
)
from neuro_sdk.url_utils import _extract_path, normalize_local_path_uri
from neuro_sdk.utils import AsyncContextManager

from .config import Config
from .core import _Core
from .errors import NDJSONError, ResourceNotFound
from .utils import (
    NoPublicConstructor,
    asyncgeneratorcontextmanager,
    queue_calls,
    retries,
)

if sys.version_info >= (3, 7):
    from contextlib import asynccontextmanager
else:
    from async_generator import asynccontextmanager


logger = logging.getLogger(__name__)


@dataclass(frozen=True)  # type: ignore
class BucketEntry(abc.ABC):
    key: str
    bucket: "Bucket"
    size: int
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None

    @property
    def name(self) -> str:
        return PurePosixPath(self.key).name

    @property
    def uri(self) -> URL:
        # Bucket key is an arbitrary string, so it can start with "/",
        # so we have to use this way to append it to bucket url
        return URL(str(self.bucket.uri) + "/" + self.key)

    @abc.abstractmethod
    def is_file(self) -> bool:
        pass

    @abc.abstractmethod
    def is_dir(self) -> bool:
        pass


class BlobObject(BucketEntry):
    def is_file(self) -> bool:
        return not self.is_dir()

    def is_dir(self) -> bool:
        return self.key.endswith("/") and self.size == 0


class BlobCommonPrefix(BucketEntry):
    size: int = 0
    # This is "folder" analog in blobs
    # objects of this type will be only returned in
    # non recursive look-ups, to group multiple keys
    # in single entry.

    def is_file(self) -> bool:
        return False

    def is_dir(self) -> bool:
        return True


MAX_OPEN_FILES = 20
READ_SIZE = 2 ** 20  # 1 MiB


class BucketProvider(abc.ABC):
    """
    Defines how to execute generic blob operations in a specific bucket provider
    """

    @abc.abstractmethod
    def list_blobs(
        self, prefix: str, recursive: bool = False, limit: Optional[int] = None
    ) -> AsyncContextManager[AsyncIterator[BucketEntry]]:
        pass

    @abc.abstractmethod
    async def head_blob(self, key: str) -> BucketEntry:
        pass

    @abc.abstractmethod
    async def put_blob(
        self,
        key: str,
        body: Union[AsyncIterator[bytes], bytes],
        size: Optional[int] = None,
    ) -> None:
        pass

    @abc.abstractmethod
    def fetch_blob(
        self, key: str, offset: int = 0, size: Optional[int] = None
    ) -> AsyncContextManager[AsyncIterator[bytes]]:
        pass


class BucketOperations:
    def __init__(self, bucket: "Bucket", provider: BucketProvider) -> None:
        self._bucket = bucket
        self._provider = provider
        self._file_sem = asyncio.BoundedSemaphore(MAX_OPEN_FILES)
        self._min_time_diff = 0.0
        self._max_time_diff = 0.0

    def head_blob(self, key: str) -> Awaitable[BucketEntry]:
        return self._provider.head_blob(key)

    def list_blobs(
        self, prefix: str, recursive: bool = False, limit: Optional[int] = None
    ) -> AsyncContextManager[AsyncIterator[BucketEntry]]:
        return self._provider.list_blobs(prefix, recursive, limit)

    @asyncgeneratorcontextmanager
    async def glob_blobs(self, pattern: str) -> AsyncIterator[BucketEntry]:
        async with self._glob_blobs("", pattern) as it:
            async for entry in it:
                yield entry

    @asyncgeneratorcontextmanager
    async def _glob_blobs(
        self, prefix: str, pattern: str
    ) -> AsyncIterator[BucketEntry]:
        part, _, remaining = pattern.partition("/")

        if _isrecursive(part):
            # Patter starts with ** => any key may match it
            full_match = re.compile(translate(pattern)).fullmatch
            async with self.list_blobs(prefix, recursive=True) as it:
                async for entry in it:
                    if full_match(entry.key[len(prefix) :]):
                        yield entry
            return

        has_magic = _has_magic(part)
        # Optimize the prefix for matching. If we have a pattern `folder1/b*/*.json`
        # it's better to scan with prefix `folder1/b` on the 2nd step, not `folder1/`
        if has_magic:
            opt_prefix = prefix + _glob_safe_prefix(part)
        else:
            opt_prefix = prefix
        match = re.compile(translate(part)).fullmatch

        # If this is the last part in the search pattern we have to scan keys, not
        # just prefixes
        if not remaining:
            async with self.list_blobs(opt_prefix, recursive=False) as it:
                async for entry in it:
                    if match(entry.name):
                        yield entry
            return

        # We can be sure no blobs on this level will match the pattern, as results are
        # deeper down the tree. Recursively scan folders only.
        if has_magic:
            async with self.list_blobs(opt_prefix, recursive=False) as it:
                async for entry in it:
                    if not entry.is_dir() or not match(entry.name):
                        continue
                    async with self._glob_blobs(entry.key, remaining) as blob_iter:
                        async for blob in blob_iter:
                            yield blob
        else:
            async with self._glob_blobs(prefix + part + "/", remaining) as blob_iter:
                async for blob in blob_iter:
                    yield blob

    async def _check_is_existing_file(self, path: Path) -> None:
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

    def _check_upload(
        self, local: os.stat_result, remote: BucketEntry
    ) -> Optional[int]:
        if (
            remote.modified_at is None
            or local.st_mtime - remote.modified_at.timestamp()
            > self._min_time_diff - TIME_THRESHOLD
        ):
            # Local is likely newer.
            return 0
        # Remote is definitely newer.
        return None

    def _check_download(
        self, local: os.stat_result, remote: BucketEntry, update: bool, continue_: bool
    ) -> Optional[int]:
        # Add 1 because remote.modification_time has been truncated
        # and can be up to 1 second less than the actual value.
        if (
            remote.modified_at is None
            or local.st_mtime - remote.modified_at.timestamp()
            < self._max_time_diff + TIME_THRESHOLD + 1.0
        ):
            # Remote is likely newer.
            return 0
        # Local is definitely newer.
        if update:
            return None
        if continue_:
            if local.st_size == remote.size:  # complete
                return None
            if local.st_size < remote.size:  # partial
                return local.st_size
        return 0

    @asyncgeneratorcontextmanager
    async def _iterate_file(
        self,
        src: Path,
        dst_uri: URL,
        size: int,
        *,
        progress: _AsyncAbstractFileProgress,
    ) -> AsyncIterator[bytes]:
        loop = asyncio.get_event_loop()
        src_url = URL(src.as_uri())
        async with self._file_sem:
            with src.open("rb") as stream:
                await progress.start(StorageProgressStart(src_url, dst_uri, size))
                chunk = await loop.run_in_executor(None, stream.read, READ_SIZE)
                pos = len(chunk)
                while chunk:
                    await progress.step(
                        StorageProgressStep(src_url, dst_uri, pos, size)
                    )
                    yield chunk
                    chunk = await loop.run_in_executor(None, stream.read, READ_SIZE)
                    pos += len(chunk)
                await progress.complete(StorageProgressComplete(src_url, dst_uri, size))

    async def upload_file(
        self,
        src: URL,
        dst: PurePosixPath,
        *,
        update: bool = False,
        progress: Optional[AbstractFileProgress] = None,
    ) -> None:
        src = normalize_local_path_uri(src)
        dst_key = str(dst).lstrip("/")

        src_path = _extract_path(src)
        await self._check_is_existing_file(src_path)

        if await self.is_dir(dst_key):
            raise IsADirectoryError(errno.EISDIR, "Is a directory", dst)

        # TODO: extract method
        if update:
            try:
                dst_stat = await self._provider.head_blob(key=dst_key)
            except ResourceNotFound:
                pass
            else:
                try:
                    src_stat = src_path.stat()
                except OSError:
                    pass
                else:
                    if S_ISREG(src_stat.st_mode):
                        offset = self._check_upload(src_stat, dst_stat)
                        if offset is None:
                            return

        async_progress: _AsyncAbstractFileProgress
        queue, async_progress = queue_calls(progress)
        await run_progress(
            queue, self._upload_file(src_path, dst_key, progress=async_progress)
        )

    async def _upload_file(
        self,
        src_path: Path,
        dst: str,
        *,
        progress: _AsyncAbstractFileProgress,
    ) -> None:
        size = src_path.stat().st_size

        for retry in retries(f"Fail to upload {dst}"):
            async with retry:
                async with self._iterate_file(
                    src_path, self._bucket.uri / dst, size, progress=progress
                ) as body:
                    await self._provider.put_blob(
                        key=dst,
                        body=body,
                        size=size,
                    )

    async def upload_dir(
        self,
        src: URL,
        dst: PurePosixPath,
        *,
        update: bool = False,
        filter: Optional[AsyncFilterFunc] = None,
        ignore_file_names: AbstractSet[str] = frozenset(),
        progress: Optional[AbstractRecursiveFileProgress] = None,
    ) -> None:
        src = normalize_local_path_uri(src)
        dst_key = str(dst).lstrip("/")
        path = _extract_path(src).resolve()
        if not path.exists():
            raise FileNotFoundError(errno.ENOENT, "No such file", str(path))
        if not path.is_dir():
            raise NotADirectoryError(errno.ENOTDIR, "Not a directory", str(path))

        if filter is None:
            filter = _always
        if ignore_file_names:
            filter = load_parent_ignore_files(filter, ignore_file_names, path)

        async_progress: _AsyncAbstractRecursiveFileProgress
        queue, async_progress = queue_calls(progress)
        await run_progress(
            queue,
            self._upload_dir(
                src,
                path,
                dst_key,
                "",
                update=update,
                filter=filter,
                ignore_file_names=ignore_file_names,
                progress=async_progress,
            ),
        )

    async def _upload_dir(
        self,
        src: URL,
        src_path: Path,
        dst: str,
        rel_path: str,
        *,
        update: bool,
        filter: AsyncFilterFunc,
        ignore_file_names: AbstractSet[str],
        progress: _AsyncAbstractRecursiveFileProgress,
    ) -> None:
        tasks = []
        dst_uri = URL(str(self._bucket.uri) + dst)  # Key can start with "/"
        dst_files = {}
        if update:
            for retry in retries(f"Fail to list {dst}"):
                async with retry:
                    async with self.list_blobs(dst, recursive=False) as it:
                        dst_files = {x.name: x async for x in it}
        try:
            await self._provider.head_blob(dst)
        except ResourceNotFound:
            pass
        else:
            raise NotADirectoryError(errno.ENOTDIR, "Not a directory", dst)

        await progress.enter(StorageProgressEnterDir(src, dst_uri))
        loop = asyncio.get_event_loop()
        async with self._file_sem:
            folder = await loop.run_in_executor(None, lambda: list(src_path.iterdir()))

        if ignore_file_names:
            for child in folder:
                if child.name in ignore_file_names and child.is_file():
                    logger.debug(f"Load ignore file {rel_path}{child.name}")
                    file_filter = FileFilter(filter)
                    file_filter.read_from_file(child, prefix=rel_path)
                    filter = file_filter.match

        for child in folder:
            name = child.name
            child_rel_path = f"{rel_path}{name}"
            if child.is_dir():
                child_rel_path += "/"
            if not await filter(child_rel_path):
                logger.debug(f"Skip {child_rel_path}")
                continue
            if child.is_file():
                if update and name in dst_files:
                    offset = self._check_upload(child.stat(), dst_files[name])
                    if offset is None:
                        continue
                tasks.append(
                    self._upload_file(
                        src_path / name, dst + "/" + name, progress=progress
                    )
                )
            elif child.is_dir():
                tasks.append(
                    self._upload_dir(
                        src / name,
                        src_path / name,
                        dst + "/" + name,
                        child_rel_path,
                        update=update,
                        filter=filter,
                        ignore_file_names=ignore_file_names,
                        progress=progress,
                    )
                )
            else:
                await progress.fail(
                    StorageProgressFail(
                        src / name,
                        dst_uri / name,
                        f"Cannot upload {child}, not regular file/directory",
                    )
                )
        await run_concurrently(tasks)
        await progress.leave(StorageProgressLeaveDir(src, dst_uri))

    async def download_file(
        self,
        src: PurePosixPath,
        dst: URL,
        *,
        update: bool = False,
        continue_: bool = False,
        progress: Optional[AbstractFileProgress] = None,
    ) -> None:
        src_key = str(src).lstrip("/")

        if await self.is_dir(src_key):
            raise IsADirectoryError(
                errno.EISDIR, "Is a directory, use recursive copy:", str(src)
            )

        dst = normalize_local_path_uri(dst)
        path = _extract_path(dst)
        src_stat = await self.head_blob(key=src_key)

        offset: Optional[int] = 0
        if update or continue_:
            try:
                dst_stat = path.stat()
            except OSError:
                pass
            else:
                if S_ISREG(dst_stat.st_mode):
                    offset = self._check_download(dst_stat, src_stat, update, continue_)
        if offset is None:
            return

        async_progress: _AsyncAbstractFileProgress
        queue, async_progress = queue_calls(progress)
        await run_progress(
            queue,
            self._download_file(
                src_key, dst, path, src_stat.size, offset, progress=async_progress
            ),
        )

    async def _download_file(
        self,
        src: str,
        dst: URL,
        dst_path: Path,
        size: int,
        offset: int,
        *,
        progress: _AsyncAbstractFileProgress,
    ) -> None:
        loop = asyncio.get_event_loop()
        src_uri = self._bucket.uri / src
        async with self._file_sem:
            await progress.start(StorageProgressStart(src_uri, dst, size))
            with dst_path.open("rb+" if offset else "wb") as stream:
                if offset:
                    stream.seek(offset)
                for retry in retries(f"Fail to download {src}"):
                    pos = stream.tell()
                    if pos >= size:
                        break
                    async with retry:
                        async with self._provider.fetch_blob(key=src, offset=pos) as it:
                            async for chunk in it:
                                pos += len(chunk)
                                await progress.step(
                                    StorageProgressStep(src_uri, dst, pos, size)
                                )
                                await loop.run_in_executor(None, stream.write, chunk)
                                if chunk:
                                    retry.reset()
            await progress.complete(StorageProgressComplete(src_uri, dst, size))

    async def download_dir(
        self,
        src: PurePosixPath,
        dst: URL,
        *,
        update: bool = False,
        continue_: bool = False,
        filter: Optional[AsyncFilterFunc] = None,
        progress: Optional[AbstractRecursiveFileProgress] = None,
    ) -> None:
        if filter is None:
            filter = _always
        src_key = str(src).lstrip("/")
        dst = normalize_local_path_uri(dst)
        path = _extract_path(dst)
        async_progress: _AsyncAbstractRecursiveFileProgress
        queue, async_progress = queue_calls(progress)
        await run_progress(
            queue,
            self._download_dir(
                src_key,
                dst,
                path,
                update=update,
                continue_=continue_,
                filter=filter,
                progress=async_progress,
            ),
        )

    async def _download_dir(
        self,
        src: str,
        dst: URL,
        dst_path: Path,
        *,
        update: bool,
        continue_: bool,
        filter: AsyncFilterFunc,
        progress: _AsyncAbstractRecursiveFileProgress,
    ) -> None:
        src_uri = self._bucket.uri / src
        dst_path.mkdir(parents=True, exist_ok=True)
        await progress.enter(StorageProgressEnterDir(src_uri, dst))
        tasks = []
        if update or continue_:
            loop = asyncio.get_event_loop()
            async with self._file_sem:
                dst_files = await loop.run_in_executor(
                    None,
                    lambda: {
                        item.name: item for item in dst_path.iterdir() if item.is_file()
                    },
                )

        prefix_path = src.strip("/")
        # If we are downloading the whole bucket we need to specify an empty prefix '',
        # not "/", thus only add it if path not empty
        if prefix_path:
            prefix_path += "/"
        for retry in retries(f"Fail to list {src}"):
            async with retry, self.list_blobs(
                prefix=prefix_path, recursive=False
            ) as it:
                async for entry in it:
                    # Skip "folder" keys, as they can be returned back as they
                    # have same prefix
                    if entry.key == prefix_path:
                        continue

                    name = entry.name
                    if entry.is_dir():
                        name += "/"
                    if not await filter(name):
                        logging.debug(f"Skip {name}")
                        continue
                    if entry.is_file():
                        offset: Optional[int] = 0
                        if (update or continue_) and name in dst_files:
                            offset = self._check_download(
                                dst_files[name].stat(), entry, update, continue_
                            )
                        if offset is None:
                            continue
                        tasks.append(
                            self._download_file(
                                entry.key,
                                dst / name,
                                dst_path / name,
                                entry.size,
                                offset,
                                progress=progress,
                            )
                        )
                    else:
                        tasks.append(
                            self._download_dir(
                                entry.key,
                                dst / name,
                                dst_path / name,
                                update=update,
                                continue_=continue_,
                                filter=filter,
                                progress=progress,
                            )
                        )
        await run_concurrently(tasks)
        await progress.leave(StorageProgressLeaveDir(src_uri, dst))

    async def mkdir(self, key_path: PurePosixPath) -> None:
        key = str(key_path) + "/"
        if not key.strip("/"):
            raise ValueError("Can not create a bucket root folder")
        await self._provider.put_blob(key=key, body=b"")

    async def is_dir(self, key: str) -> bool:
        if key.endswith("/") or key == "":
            return True
        async with self.list_blobs(prefix=key + "/", recursive=False, limit=1) as it:
            return bool([entry async for entry in it])


class AWSS3Provider(BucketProvider):
    def __init__(self, client: AioBaseClient, bucket: "Bucket") -> None:
        self._bucket = bucket
        self._client = client

    @property
    def _bucket_name(self) -> str:
        return self._bucket.credentials["bucket_name"]

    @classmethod
    @asynccontextmanager
    async def create(cls, bucket: "Bucket") -> AsyncIterator["AWSS3Provider"]:
        session = aiobotocore.get_session()
        async with session.create_client(
            "s3",
            aws_access_key_id=bucket.credentials["access_key_id"],
            aws_secret_access_key=bucket.credentials["secret_access_key"],
        ) as client:
            yield cls(client, bucket)

    @asyncgeneratorcontextmanager
    async def list_blobs(
        self, prefix: str, recursive: bool = False, limit: Optional[int] = None
    ) -> AsyncIterator[BucketEntry]:
        paginator = self._client.get_paginator("list_objects_v2")
        kwargs = dict(Bucket=self._bucket_name, Prefix=prefix)
        if not recursive:
            kwargs["Delimiter"] = "/"
        cnt = 0
        async for result in paginator.paginate(**kwargs):
            for common_prefix in result.get("CommonPrefixes", []):
                yield BlobCommonPrefix(
                    bucket=self._bucket,
                    size=0,
                    key=common_prefix["Prefix"],
                )
                cnt += 1
                if cnt == limit:
                    return
            for blob in result.get("Contents", []):
                yield BlobObject(
                    bucket=self._bucket,
                    key=blob["Key"],
                    modified_at=blob["LastModified"],
                    size=blob["Size"],
                )
                cnt += 1
                if cnt == limit:
                    return

    async def head_blob(self, key: str) -> BucketEntry:
        try:
            blob = await self._client.head_object(Bucket=self._bucket_name, Key=key)
            return BlobObject(
                bucket=self._bucket,
                key=blob["Key"],
                modified_at=blob["LastModified"],
                size=blob["Size"],
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise ResourceNotFound(
                    f"There is no object with key {key} in bucket {self._bucket.name}"
                )
            raise

    async def put_blob(
        self,
        key: str,
        body: Union[AsyncIterator[bytes], bytes],
        size: Optional[int] = None,
    ) -> None:
        # TODO support multipart upload
        if not isinstance(body, bytes):
            body = b"".join([chunk async for chunk in body])
        await self._client.put_object(
            Bucket=self._bucket_name,
            Key=key,
            Body=body,
        )

    @asyncgeneratorcontextmanager
    async def fetch_blob(
        self, key: str, offset: int = 0, size: Optional[int] = None
    ) -> AsyncIterator[bytes]:
        response = await self._client.get_object(
            Bucket=self._bucket_name, Key=key, Range=f"bytes={offset}-"
        )
        # this will ensure the connection is correctly re-used/closed
        async with response["Body"] as stream:
            async for chunk in stream.iter_chunks():
                yield chunk[0]


@dataclass(frozen=True)
class Bucket:
    id: str
    owner: str
    cluster_name: str
    provider: "Bucket.Provider"
    credentials: Mapping[str, str]
    created_at: datetime
    name: Optional[str] = None

    @property
    def uri(self) -> URL:
        return URL(f"blob://{self.cluster_name}/{self.owner}/{self.id}")

    class Provider(str, enum.Enum):
        AWS = "aws"

    @asynccontextmanager
    async def get_operations(self) -> AsyncIterator[BucketOperations]:
        async with AWSS3Provider.create(self) as provider:
            yield BucketOperations(self, provider)


class Buckets(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: Config) -> None:
        self._core = core
        self._config = config

    def _parse_bucket_payload(self, payload: Mapping[str, Any]) -> Bucket:
        return Bucket(
            id=payload["id"],
            owner=payload["owner"],
            name=payload.get("name"),
            created_at=isoparse(payload["created_at"]),
            provider=Bucket.Provider(payload["provider"]),
            cluster_name=self._config.cluster_name,
            credentials=payload["credentials"],
        )

    def _get_buckets_url(self, cluster_name: Optional[str]) -> URL:
        if cluster_name is None:
            cluster_name = self._config.cluster_name
        return self._config.get_cluster(cluster_name).buckets_url

    @asyncgeneratorcontextmanager
    async def list(self, cluster_name: Optional[str] = None) -> AsyncIterator[Bucket]:
        url = self._get_buckets_url(cluster_name)
        auth = await self._config._api_auth()
        headers = {"Accept": "application/x-ndjson"}
        async with self._core.request("GET", url, headers=headers, auth=auth) as resp:
            if resp.headers.get("Content-Type", "").startswith("application/x-ndjson"):
                async for line in resp.content:
                    server_message = json.loads(line)
                    if "error" in server_message:
                        raise NDJSONError(server_message["error"])
                    yield self._parse_bucket_payload(server_message)
            else:
                ret = await resp.json()
                for bucket_data in ret:
                    yield self._parse_bucket_payload(bucket_data)

    async def create(
        self,
        name: Optional[str] = None,
        cluster_name: Optional[str] = None,
    ) -> Bucket:
        url = self._get_buckets_url(cluster_name)
        auth = await self._config._api_auth()
        data = {
            "name": name,
        }
        async with self._core.request("POST", url, auth=auth, json=data) as resp:
            payload = await resp.json()
            return self._parse_bucket_payload(payload)

    async def get(
        self, bucket_id_or_name: str, cluster_name: Optional[str] = None
    ) -> Bucket:
        url = self._get_buckets_url(cluster_name) / bucket_id_or_name
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            payload = await resp.json()
            return self._parse_bucket_payload(payload)

    async def rm(
        self, bucket_id_or_name: str, cluster_name: Optional[str] = None
    ) -> None:
        url = self._get_buckets_url(cluster_name) / bucket_id_or_name
        auth = await self._config._api_auth()
        async with self._core.request("DELETE", url, auth=auth):
            pass
