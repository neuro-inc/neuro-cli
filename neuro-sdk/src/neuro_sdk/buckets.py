import abc
import enum
import json
import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from typing import AbstractSet, Any, AsyncIterator, Mapping, Optional, Tuple, Union

import aiobotocore as aiobotocore
import botocore.exceptions
from aiobotocore.client import AioBaseClient
from dateutil.parser import isoparse
from yarl import URL

from neuro_sdk import AbstractRecursiveFileProgress
from neuro_sdk.abc import AbstractFileProgress
from neuro_sdk.file_filter import (
    AsyncFilterFunc,
    _glob_safe_prefix,
    _has_magic,
    _isrecursive,
    translate,
)
from neuro_sdk.file_utils import FileSystem, FileTransferer, LocalFS
from neuro_sdk.url_utils import (
    _extract_path,
    normalize_blob_path_uri,
    normalize_local_path_uri,
)
from neuro_sdk.utils import AsyncContextManager

from .config import Config
from .core import _Core
from .errors import NDJSONError, ResourceNotFound
from .utils import NoPublicConstructor, asyncgeneratorcontextmanager

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

    bucket: "Bucket"

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

    @abc.abstractmethod
    async def delete_blob(
        self,
        key: str,
    ) -> None:
        pass


class BucketFS(FileSystem[PurePosixPath]):
    fs_name = "Bucket"
    supports_offset_read = True
    supports_offset_write = False

    def __init__(self, provider: BucketProvider) -> None:
        self._provider = provider

    def _as_file_key(self, path: PurePosixPath) -> str:
        if not path.is_absolute():
            path = "/" / path
        return str(path).lstrip("/")

    def _as_dir_key(self, path: PurePosixPath) -> str:
        return (self._as_file_key(path) + "/").lstrip("/")

    async def exists(self, path: PurePosixPath) -> bool:
        if self._as_dir_key(path) == "":
            return True
        try:
            await self._provider.head_blob(self._as_file_key(path))
            return True
        except ResourceNotFound:
            # Maybe this is a directory?
            async with self._provider.list_blobs(
                prefix=self._as_dir_key(path), recursive=False, limit=1
            ) as it:
                return bool([entry async for entry in it])

    async def is_dir(self, path: PurePosixPath) -> bool:
        if self._as_dir_key(path) == "":
            return True
        async with self._provider.list_blobs(
            prefix=self._as_dir_key(path), recursive=False, limit=1
        ) as it:
            return bool([entry async for entry in it])

    async def is_file(self, path: PurePosixPath) -> bool:
        try:
            await self._provider.head_blob(self._as_file_key(path))
            return True
        except ResourceNotFound:
            return False

    async def stat(self, path: PurePosixPath) -> "FileSystem.BasicStat[PurePosixPath]":
        blob = await self._provider.head_blob(self._as_file_key(path))
        return FileSystem.BasicStat(
            name=path.name,
            path=path,
            size=blob.size,
            modification_time=blob.modified_at.timestamp()
            if blob.modified_at
            else None,
        )

    @asyncgeneratorcontextmanager
    async def read_chunks(
        self, path: PurePosixPath, offset: int = 0
    ) -> AsyncIterator[bytes]:
        async with self._provider.fetch_blob(self._as_file_key(path), offset) as it:
            async for chunk in it:
                yield chunk

    async def write_chunks(
        self, path: PurePosixPath, body: AsyncIterator[bytes], offset: int = 0
    ) -> None:
        assert offset == 0, "Buckets do not support offset write"
        await self._provider.put_blob(self._as_file_key(path), body)

    @asyncgeneratorcontextmanager
    async def iter_dir(self, path: PurePosixPath) -> AsyncIterator[PurePosixPath]:
        async with self._provider.list_blobs(
            prefix=self._as_dir_key(path), recursive=False
        ) as it:
            async for item in it:
                res = PurePosixPath(item.key)
                if res != path:  # Directory can be listed as self child
                    yield res

    async def mkdir(self, path: PurePosixPath) -> None:
        key = self._as_dir_key(path)
        if key == "":
            raise ValueError("Can not create a bucket root folder")
        await self._provider.put_blob(key=key, body=b"")

    def to_url(self, path: PurePosixPath) -> URL:
        return self._provider.bucket.uri / self._as_file_key(path)

    async def get_time_diff_to_local(self) -> float:
        return 0  # TODO: implement it

    def parent(self, path: PurePosixPath) -> PurePosixPath:
        return path.parent

    def name(self, path: PurePosixPath) -> str:
        return path.name

    def child(self, path: PurePosixPath, child: str) -> PurePosixPath:
        return path / child


class AWSS3Provider(BucketProvider):
    def __init__(self, client: AioBaseClient, bucket: "Bucket") -> None:
        self.bucket = bucket
        self._client = client

    @property
    def _bucket_name(self) -> str:
        return self.bucket.credentials["bucket_name"]

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
                    bucket=self.bucket,
                    size=0,
                    key=common_prefix["Prefix"],
                )
                cnt += 1
                if cnt == limit:
                    return
            for blob in result.get("Contents", []):
                yield BlobObject(
                    bucket=self.bucket,
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
                bucket=self.bucket,
                key=key,
                modified_at=blob["LastModified"],
                size=blob["ContentLength"],
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise ResourceNotFound(
                    f"There is no object with key {key} in bucket {self.bucket.name}"
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
        async with response["Body"] as stream:
            async for chunk in stream.iter_chunks():
                yield chunk[0]

    async def delete_blob(self, key: str) -> None:
        await self._client.delete_object(Bucket=self._bucket_name, Key=key)


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
        return URL(f"blob://{self.cluster_name}/{self.owner}/{self.name or self.id}")

    class Provider(str, enum.Enum):
        AWS = "aws"


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

    # Helper functions

    @asynccontextmanager
    async def _get_provider(
        self, bucket_name: str, cluster_name: Optional[str] = None
    ) -> AsyncIterator[BucketProvider]:
        bucket = await self.get(bucket_name, cluster_name)
        if bucket.provider == Bucket.Provider.AWS:
            async with AWSS3Provider.create(bucket) as provider:
                yield provider
        else:
            assert False, f"Unknown provider {bucket.provider}"

    @asynccontextmanager
    async def _get_bucket_fs(
        self, bucket_name: str, cluster_name: Optional[str] = None
    ) -> AsyncIterator[FileSystem[PurePosixPath]]:
        async with self._get_provider(bucket_name, cluster_name) as provider:
            yield BucketFS(provider)

    def _split_blob_uri(self, uri: URL) -> Tuple[str, str, str]:
        uri = normalize_blob_path_uri(
            uri, self._config.username, self._config.cluster_name
        )
        cluster_name = uri.host
        assert cluster_name
        parts = uri.path.lstrip("/").split("/", 2)
        if len(parts) == 3:
            _, bucket_id, key = parts
        else:
            _, bucket_id = parts
            key = ""
        return cluster_name, bucket_id, key

    # Low level operations

    async def head_blob(
        self, bucket_name: str, key: str, cluster_name: Optional[str] = None
    ) -> BucketEntry:
        async with self._get_provider(bucket_name, cluster_name) as provider:
            return await provider.head_blob(key)

    async def put_blob(
        self,
        bucket_name: str,
        key: str,
        body: Union[AsyncIterator[bytes], bytes],
        cluster_name: Optional[str] = None,
    ) -> None:
        async with self._get_provider(bucket_name, cluster_name) as provider:
            await provider.put_blob(key, body)

    @asyncgeneratorcontextmanager
    async def fetch_blob(
        self,
        bucket_name: str,
        key: str,
        offset: int = 0,
        cluster_name: Optional[str] = None,
    ) -> AsyncIterator[bytes]:
        async with self._get_provider(bucket_name, cluster_name) as provider:
            async with provider.fetch_blob(key, offset=offset) as it:
                async for chunk in it:
                    yield chunk

    async def delete_blob(
        self, bucket_name: str, key: str, cluster_name: Optional[str] = None
    ) -> None:
        async with self._get_provider(bucket_name, cluster_name) as provider:
            return await provider.delete_blob(key)

    # Listing operations

    @asyncgeneratorcontextmanager
    async def list_blobs(
        self,
        uri: URL,
        recursive: bool = False,
        limit: Optional[int] = None,
    ) -> AsyncIterator[BucketEntry]:
        cluster_name, bucket_name, key = self._split_blob_uri(uri)
        async with self._get_provider(bucket_name, cluster_name) as provider:
            async with provider.list_blobs(key, recursive=recursive, limit=limit) as it:
                async for entry in it:
                    yield entry

    @asyncgeneratorcontextmanager
    async def glob_blobs(self, uri: URL) -> AsyncIterator[BucketEntry]:
        cluster_name, bucket_name, key = self._split_blob_uri(uri)
        if _has_magic(bucket_name):
            raise ValueError(
                "You can not glob on bucket names. Please provide name explicitly."
            )

        async with self._get_provider(bucket_name, cluster_name) as provider:
            async with self._glob_blobs("", key, provider) as it:
                async for entry in it:
                    yield entry

    @asyncgeneratorcontextmanager
    async def _glob_blobs(
        self, prefix: str, pattern: str, provider: BucketProvider
    ) -> AsyncIterator[BucketEntry]:
        # TODO: factor out code with storage

        part, _, remaining = pattern.partition("/")

        if _isrecursive(part):
            # Patter starts with ** => any key may match it
            full_match = re.compile(translate(pattern)).fullmatch
            async with provider.list_blobs(prefix, recursive=True) as it:
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
            async with provider.list_blobs(opt_prefix, recursive=False) as it:
                async for entry in it:
                    if match(entry.name) and not entry.key == opt_prefix:
                        yield entry
            return

        # We can be sure no blobs on this level will match the pattern, as results are
        # deeper down the tree. Recursively scan folders only.
        if has_magic:
            async with provider.list_blobs(opt_prefix, recursive=False) as it:
                async for entry in it:
                    if not entry.is_dir() or not match(entry.name):
                        continue
                    async with self._glob_blobs(
                        entry.key, remaining, provider
                    ) as blob_iter:
                        async for blob in blob_iter:
                            yield blob
        else:
            async with self._glob_blobs(
                prefix + part + "/", remaining, provider
            ) as blob_iter:
                async for blob in blob_iter:
                    yield blob

    # High level transfer operations

    async def upload_file(
        self,
        src: URL,
        dst: URL,
        *,
        update: bool = False,
        progress: Optional[AbstractFileProgress] = None,
    ) -> None:
        src = normalize_local_path_uri(src)
        cluster_name, bucket_name, key = self._split_blob_uri(dst)
        async with self._get_bucket_fs(bucket_name, cluster_name) as bucket_fs:
            transferer = FileTransferer(LocalFS(), bucket_fs)
            await transferer.transfer_file(
                src=_extract_path(src),
                dst=PurePosixPath(key),
                update=update,
                progress=progress,
            )

    async def download_file(
        self,
        src: URL,
        dst: URL,
        *,
        update: bool = False,
        continue_: bool = False,
        progress: Optional[AbstractFileProgress] = None,
    ) -> None:
        cluster_name, bucket_name, key = self._split_blob_uri(src)
        dst = normalize_local_path_uri(dst)
        async with self._get_bucket_fs(bucket_name, cluster_name) as bucket_fs:
            transferer = FileTransferer(bucket_fs, LocalFS())
            await transferer.transfer_file(
                src=PurePosixPath(key),
                dst=_extract_path(dst),
                update=update,
                continue_=continue_,
                progress=progress,
            )

    async def upload_dir(
        self,
        src: URL,
        dst: URL,
        *,
        update: bool = False,
        filter: Optional[AsyncFilterFunc] = None,
        ignore_file_names: AbstractSet[str] = frozenset(),
        progress: Optional[AbstractRecursiveFileProgress] = None,
    ) -> None:
        src = normalize_local_path_uri(src)
        cluster_name, bucket_name, key = self._split_blob_uri(dst)
        async with self._get_bucket_fs(bucket_name, cluster_name) as bucket_fs:
            transferer = FileTransferer(LocalFS(), bucket_fs)
            await transferer.transfer_dir(
                src=_extract_path(src),
                dst=PurePosixPath(key),
                filter=filter,
                ignore_file_names=ignore_file_names,
                update=update,
                progress=progress,
            )

    async def download_dir(
        self,
        src: URL,
        dst: URL,
        *,
        update: bool = False,
        continue_: bool = False,
        filter: Optional[AsyncFilterFunc] = None,
        progress: Optional[AbstractRecursiveFileProgress] = None,
    ) -> None:
        cluster_name, bucket_name, key = self._split_blob_uri(src)
        dst = normalize_local_path_uri(dst)
        async with self._get_bucket_fs(bucket_name, cluster_name) as bucket_fs:
            transferer = FileTransferer(bucket_fs, LocalFS())
            await transferer.transfer_dir(
                src=PurePosixPath(key),
                dst=_extract_path(dst),
                update=update,
                continue_=continue_,
                filter=filter,
                progress=progress,
            )

    async def blob_is_dir(self, uri: URL) -> bool:
        cluster_name, bucket_name, key = self._split_blob_uri(uri)
        if key.endswith("/"):
            return True
        async with self._get_bucket_fs(bucket_name, cluster_name) as bucket_fs:
            return await bucket_fs.is_dir(PurePosixPath(key))
