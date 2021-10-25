import abc
import asyncio
import base64
import enum
import json
import logging
import re
import secrets
import sys
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from io import BytesIO
from pathlib import PurePosixPath
from typing import (
    AbstractSet,
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Iterable,
    List,
    Mapping,
    Optional,
    Tuple,
    Union,
)

import aiobotocore as aiobotocore
import botocore.exceptions
from aiobotocore.client import AioBaseClient
from aiobotocore.credentials import AioCredentials, AioRefreshableCredentials
from aiohttp import ClientResponse, ClientSession
from azure.core.credentials import AzureSasCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobBlock
from azure.storage.blob.aio import ContainerClient
from azure.storage.blob.aio._list_blobs_helper import BlobPrefix
from dateutil.parser import isoparse
from google.auth.transport._aiohttp_requests import Request
from google.oauth2._service_account_async import Credentials as SACredentials
from yarl import URL

from neuro_sdk import AbstractRecursiveFileProgress, file_utils
from neuro_sdk.abc import AbstractDeleteProgress, AbstractFileProgress
from neuro_sdk.file_filter import (
    AsyncFilterFunc,
    _glob_safe_prefix,
    _has_magic,
    _isrecursive,
    translate,
)
from neuro_sdk.file_utils import FileSystem, FileTransferer, LocalFS
from neuro_sdk.url_utils import _extract_path, normalize_local_path_uri
from neuro_sdk.utils import AsyncContextManager

from .config import Config
from .core import _Core
from .errors import NDJSONError, ResourceNotFound
from .parser import Parser
from .utils import NoPublicConstructor, asyncgeneratorcontextmanager

if sys.version_info >= (3, 7):
    from contextlib import AsyncExitStack, asynccontextmanager
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
    ) -> None:
        pass

    @abc.abstractmethod
    def fetch_blob(
        self, key: str, offset: int = 0
    ) -> AsyncContextManager[AsyncIterator[bytes]]:
        pass

    @abc.abstractmethod
    async def delete_blob(
        self,
        key: str,
    ) -> None:
        pass

    @abc.abstractmethod
    async def get_time_diff_to_local(self) -> Tuple[float, float]:
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

    async def rmdir(self, path: PurePosixPath) -> None:
        key = self._as_dir_key(path)
        if key == "":
            return  # Root dir cannot be removed
        try:
            await self._provider.delete_blob(key=key)
        except ResourceNotFound:
            pass  # Dir already removed/was a prefix - just ignore

    async def rm(self, path: PurePosixPath) -> None:
        key = self._as_file_key(path)
        await self._provider.delete_blob(key=key)

    def to_url(self, path: PurePosixPath) -> URL:
        return self._provider.bucket.uri / self._as_file_key(path)

    async def get_time_diff_to_local(self) -> Tuple[float, float]:
        return await self._provider.get_time_diff_to_local()

    def parent(self, path: PurePosixPath) -> PurePosixPath:
        return path.parent

    def name(self, path: PurePosixPath) -> str:
        return path.name

    def child(self, path: PurePosixPath, child: str) -> PurePosixPath:
        return path / child


class MeasureTimeDiffMixin:
    def __init__(self) -> None:
        self._min_time_diff: Optional[float] = 0
        self._max_time_diff: Optional[float] = 0

    def _wrap_api_call(
        self,
        _make_call: Callable[..., Awaitable[Any]],
        get_date: Callable[[Any], datetime],
    ) -> Callable[..., Awaitable[Any]]:
        @asynccontextmanager
        async def _ctx_manager(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            yield await _make_call(*args, **kwargs)

        manager_wrapped = self._wrap_api_call_ctx_manager(_ctx_manager, get_date)

        async def _wrapper(*args: Any, **kwargs: Any) -> Any:
            async with manager_wrapped(*args, **kwargs) as res:
                return res

        return _wrapper

    def _wrap_api_call_ctx_manager(
        self,
        _make_call: Callable[..., AsyncContextManager[Any]],
        get_date: Callable[[Any], datetime],
    ) -> Callable[..., AsyncContextManager[Any]]:
        def _average(cur_approx: Optional[float], new_val: float) -> float:
            if cur_approx is None:
                return new_val
            return cur_approx * 0.9 + new_val * 0.1

        @asynccontextmanager
        async def _wrapper(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            before = time.time()
            async with _make_call(*args, **kwargs) as res:
                after = time.time()
                yield res
            try:
                server_dt = get_date(res)
            except Exception:
                pass
            else:
                server_time = server_dt.timestamp()
                # Remove 1 because server time has been truncated
                # and can be up to 1 second less than the actual value.
                self._min_time_diff = _average(
                    cur_approx=self._min_time_diff,
                    new_val=before - server_time - 1.0,
                )
                self._max_time_diff = _average(
                    cur_approx=self._min_time_diff,
                    new_val=after - server_time,
                )

        return _wrapper

    async def get_time_diff_to_local(self) -> Tuple[float, float]:
        if self._min_time_diff is None or self._max_time_diff is None:
            return 0, 0
        return self._min_time_diff, self._max_time_diff


class S3Provider(MeasureTimeDiffMixin, BucketProvider):
    def __init__(
        self, client: AioBaseClient, bucket: "Bucket", bucket_name: str
    ) -> None:
        super().__init__()
        self.bucket = bucket
        self._client = client
        self._bucket_name = bucket_name

        def _extract_date(resp: Any) -> datetime:
            date_str = resp["ResponseMetadata"]["HTTPHeaders"]["date"]
            return parsedate_to_datetime(date_str)

        client._make_api_call = self._wrap_api_call(
            client._make_api_call, _extract_date
        )

    @classmethod
    @asynccontextmanager
    async def create(
        cls,
        bucket: "Bucket",
        _get_credentials: Callable[[], Awaitable["BucketCredentials"]],
    ) -> AsyncIterator["S3Provider"]:
        initial_credentials = await _get_credentials()

        session = aiobotocore.get_session()

        if "expiration" in initial_credentials.credentials:

            def _credentials_to_meta(
                credentials: "BucketCredentials",
            ) -> Mapping[str, str]:
                return {
                    "access_key": credentials.credentials["access_key_id"],
                    "secret_key": credentials.credentials["secret_access_key"],
                    "token": credentials.credentials["session_token"],
                    "expiry_time": credentials.credentials["expiration"],
                }

            async def _refresher() -> Mapping[str, str]:
                return _credentials_to_meta(await _get_credentials())

            session._credentials = AioRefreshableCredentials.create_from_metadata(
                metadata=_credentials_to_meta(initial_credentials),
                refresh_using=_refresher,
                method="neuro-bucket-api-refresh",  # This is just a label
            )
        else:
            # Permanent credentials
            session._credentials = AioCredentials(
                access_key=initial_credentials.credentials["access_key_id"],
                secret_key=initial_credentials.credentials["secret_access_key"],
            )

        async with session.create_client(
            "s3",
            endpoint_url=initial_credentials.credentials.get("endpoint_url"),
            region_name=initial_credentials.credentials.get("region_name"),
        ) as client:
            yield cls(client, bucket, initial_credentials.credentials["bucket_name"])

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

    MIN_CHUNK_SIZE = 10 * (2 ** 20)  # 10mb

    async def put_blob(
        self,
        key: str,
        body: Union[AsyncIterator[bytes], bytes],
    ) -> None:
        if isinstance(body, bytes):
            await self._client.put_object(
                Bucket=self._bucket_name,
                Key=key,
                Body=body,
            )
            return
        upload_id = (
            await self._client.create_multipart_upload(
                Bucket=self._bucket_name,
                Key=key,
            )
        )["UploadId"]
        try:
            part_id = 1
            parts_info = []
            buffer = b""

            async def _upload_chunk() -> None:
                nonlocal buffer, part_id
                part = await self._client.upload_part(
                    Bucket=self._bucket_name,
                    Key=key,
                    UploadId=upload_id,
                    PartNumber=part_id,
                    Body=buffer,
                )
                buffer = b""
                parts_info.append({"ETag": part["ETag"], "PartNumber": part_id})
                part_id += 1

            async for chunk in body:
                buffer += chunk
                if len(buffer) > self.MIN_CHUNK_SIZE:
                    await _upload_chunk()
            if buffer or len(parts_info) == 0:
                # Either there is final part of file or file is zero-length file
                await _upload_chunk()
        except Exception:
            await self._client.abort_multipart_upload(
                Bucket=self._bucket_name,
                Key=key,
                UploadId=upload_id,
            )
            raise
        else:
            await self._client.complete_multipart_upload(
                Bucket=self._bucket_name,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={
                    "Parts": parts_info,
                },
            )

    @asyncgeneratorcontextmanager
    async def fetch_blob(self, key: str, offset: int = 0) -> AsyncIterator[bytes]:
        response = await self._client.get_object(
            Bucket=self._bucket_name,
            Key=key,
            Range=f"bytes={offset}-" if offset else "",
        )
        async with response["Body"] as stream:
            async for chunk in stream.iter_any():
                yield chunk

    async def delete_blob(self, key: str) -> None:
        await self._client.delete_object(Bucket=self._bucket_name, Key=key)


class AzureProvider(MeasureTimeDiffMixin, BucketProvider):
    def __init__(self, container_client: ContainerClient, bucket: "Bucket") -> None:
        super().__init__()
        self.bucket = bucket

        self._client = container_client

        def _extract_date(resp: Any) -> datetime:
            date_str = resp.http_response.headers["Date"]
            return parsedate_to_datetime(date_str)

        # Hack to get client-server clock difference
        container_client._client._client._pipeline.run = self._wrap_api_call(
            container_client._client._client._pipeline.run, _extract_date
        )

    @classmethod
    @asynccontextmanager
    async def create(
        cls,
        bucket: "Bucket",
        _get_credentials: Callable[[], Awaitable["BucketCredentials"]],
    ) -> AsyncIterator["AzureProvider"]:
        initial_credentials = await _get_credentials()

        async with AsyncExitStack() as exit_stack:
            credential: Union[AzureSasCredential, str]
            if "sas_token" in initial_credentials.credentials:
                sas_credential = AzureSasCredential(
                    initial_credentials.credentials["sas_token"]
                )
                credential = sas_credential

                @asynccontextmanager
                async def _token_renewer() -> AsyncIterator[None]:
                    async def renew_token_loop() -> None:
                        expiry = isoparse(initial_credentials.credentials["expiry"])
                        while True:
                            delay = (
                                expiry
                                - timedelta(minutes=10)
                                - datetime.now(timezone.utc)
                            ).total_seconds()
                            await asyncio.sleep(max(delay, 0))
                            credentials = await _get_credentials()
                            sas_credential.update(credentials.credentials["sas_token"])
                            expiry = isoparse(credentials.credentials["expiry"])

                    task = asyncio.ensure_future(renew_token_loop())
                    try:
                        yield
                    finally:
                        task.cancel()

                await exit_stack.enter_async_context(_token_renewer())
            else:
                credential = initial_credentials.credentials["credential"]

            container_client = await exit_stack.enter_async_context(
                ContainerClient(
                    account_url=initial_credentials.credentials["storage_endpoint"],
                    container_name=initial_credentials.credentials["bucket_name"],
                    credential=credential,
                )
            )
            yield cls(container_client, bucket)

    @asyncgeneratorcontextmanager
    async def list_blobs(
        self, prefix: str, recursive: bool = False, limit: Optional[int] = None
    ) -> AsyncIterator[BucketEntry]:
        if recursive:
            it = self._client.list_blobs(prefix)
        else:
            it = self._client.walk_blobs(prefix)
        count = 0
        async for item in it:
            if isinstance(item, BlobPrefix):
                entry: BucketEntry = BlobCommonPrefix(
                    bucket=self.bucket,
                    key=item.name,
                    size=0,
                )
            else:
                entry = BlobObject(
                    bucket=self.bucket,
                    key=item.name,
                    size=item.size,
                    created_at=item.creation_time,
                    modified_at=item.last_modified,
                )
            yield entry
            count += 1
            if count == limit:
                return

    async def head_blob(self, key: str) -> BucketEntry:
        try:
            blob_info = await self._client.get_blob_client(key).get_blob_properties()
            return BlobObject(
                bucket=self.bucket,
                key=blob_info.name,
                size=blob_info.size,
                created_at=blob_info.creation_time,
                modified_at=blob_info.last_modified,
            )
        except ResourceNotFoundError:
            raise ResourceNotFound(
                f"There is no object with key {key} in bucket {self.bucket.name}"
            )

    async def put_blob(
        self, key: str, body: Union[AsyncIterator[bytes], bytes]
    ) -> None:
        blob_client = self._client.get_blob_client(key)
        if isinstance(body, bytes):
            await blob_client.upload_blob(body)
        else:
            blocks = []
            async for data in body:
                block_id = secrets.token_hex(16)
                await blob_client.stage_block(block_id, data)
                blocks.append(BlobBlock(block_id=block_id))
            await blob_client.commit_block_list(blocks)

    @asyncgeneratorcontextmanager
    async def fetch_blob(self, key: str, offset: int = 0) -> AsyncIterator[bytes]:
        try:
            downloader = await self._client.get_blob_client(key).download_blob(
                offset=offset
            )
        except ResourceNotFoundError:
            raise ResourceNotFound(
                f"There is no object with key {key} in bucket {self.bucket.name}"
            )
        async for chunk in downloader.chunks():
            yield chunk

    async def delete_blob(self, key: str) -> None:
        try:
            await self._client.get_blob_client(key).delete_blob()
        except ResourceNotFoundError:
            raise ResourceNotFound(
                f"There is no object with key {key} in bucket {self.bucket.name}"
            )

    async def get_time_diff_to_local(self) -> Tuple[float, float]:
        if self._min_time_diff is None or self._max_time_diff is None:
            return 0, 0
        return self._min_time_diff, self._max_time_diff


class AutoRefreshingGCSToken(abc.ABC):
    def __init__(
        self,
    ) -> None:
        self._lock = asyncio.Lock()
        self._token = ""

    @abc.abstractmethod
    def _refresh_required(self) -> bool:
        pass

    @abc.abstractmethod
    async def _do_refresh(self) -> None:
        pass

    async def _refresh_if_needed(self) -> None:
        if not self._refresh_required():
            return
        async with self._lock:
            if not self._refresh_required():
                return
            await self._do_refresh()

    async def get_token(self) -> str:
        await self._refresh_if_needed()
        return self._token


class NeuroAutoRefreshingGCSToken(AutoRefreshingGCSToken):
    REFRESH_DELAY = timedelta(minutes=10)

    def __init__(
        self,
        initial_credentials: "BucketCredentials",
        get_credentials: Callable[[], Awaitable["BucketCredentials"]],
    ):
        super().__init__()
        self._parse_credentials(initial_credentials)
        self._get_credentials = get_credentials

    def _parse_credentials(self, credentials: "BucketCredentials") -> None:
        self._token = credentials.credentials["access_token"]
        self._expiry = isoparse(credentials.credentials["expire_time"])

    def _refresh_required(self) -> bool:
        return (
            self._token is None
            or (self._expiry - datetime.now(timezone.utc)) < self.REFRESH_DELAY
        )

    async def _do_refresh(self) -> None:
        self._parse_credentials(await self._get_credentials())


class ServiceAccountRefreshingGCSToken(AutoRefreshingGCSToken):
    def __init__(self, key_data_json_b64: str, request: Request) -> None:
        super().__init__()
        self._credential: SACredentials = SACredentials.from_service_account_info(
            json.loads(base64.b64decode(key_data_json_b64).decode())
        )
        self._credential = self._credential.with_scopes(
            ["https://www.googleapis.com/auth/devstorage.read_write"]
        )
        self._request = request

    async def _do_refresh(self) -> None:
        await self._credential.refresh(self._request)
        self._token = self._credential.token

    def _refresh_required(self) -> bool:
        return not self._token or not self._credential.valid


class GCSProvider(MeasureTimeDiffMixin, BucketProvider):
    BASE_URL = "https://storage.googleapis.com/storage/v1"
    UPLOAD_BASE_URL = "https://storage.googleapis.com/upload/storage/v1"
    MIN_CHUNK_SIZE = 10 * 262144

    def __init__(
        self,
        session: ClientSession,
        token: AutoRefreshingGCSToken,
        bucket: "Bucket",
        gcs_bucket_name: str,
    ) -> None:
        super().__init__()
        self.bucket = bucket
        self._session = session
        self._token = token
        self._gcs_bucket_name = gcs_bucket_name

        def _extract_date(resp: ClientResponse) -> datetime:
            date_str = resp.headers["Date"]
            return parsedate_to_datetime(date_str)

        self._request = self._wrap_api_call_ctx_manager(  # type: ignore
            self._request, _extract_date
        )

    @asynccontextmanager
    async def _request(
        self,
        method: str,
        url: str,
        params: Optional[Mapping[str, str]] = None,
        headers: Optional[Mapping[str, str]] = None,
        json: Optional[Mapping[str, Any]] = None,
        data: Optional[Any] = None,
    ) -> AsyncIterator[ClientResponse]:
        async with self._session.request(
            method,
            url,
            params=params,
            headers=headers,
            json=json,
            data=data,
        ) as resp:
            if resp.status == 404:
                raise ResourceNotFound
            if resp.status > 400:
                # Some error response are OK (404 for example), so just log here
                response_text = await resp.text()
                logger.info(f"Request to GCS failed {method} {url}: {response_text}")
            resp.raise_for_status()
            yield resp

    @classmethod
    @asynccontextmanager
    async def create(
        cls,
        bucket: "Bucket",
        _get_credentials: Callable[[], Awaitable["BucketCredentials"]],
    ) -> AsyncIterator["GCSProvider"]:
        initial_credentials = await _get_credentials()

        async with ClientSession(auto_decompress=False) as session:
            token: AutoRefreshingGCSToken
            if "key_data" in initial_credentials.credentials:
                raw = initial_credentials.credentials["key_data"]
                token = ServiceAccountRefreshingGCSToken(raw, request=Request(session))
            else:
                token = NeuroAutoRefreshingGCSToken(
                    initial_credentials, _get_credentials
                )

            yield cls(
                session, token, bucket, initial_credentials.credentials["bucket_name"]
            )

    async def _get_auth_headers(self) -> Mapping[str, str]:
        token = await self._token.get_token()
        return {"Authorization": f"Bearer {token}"}

    def _parse_obj(self, data: Mapping[str, Any]) -> BlobObject:
        created_at = isoparse(data["timeCreated"])
        return BlobObject(
            bucket=self.bucket,
            key=data["name"],
            size=int(data["size"]),
            created_at=created_at,
            modified_at=created_at,  # blobs are immutable
        )

    @asyncgeneratorcontextmanager
    async def list_blobs(
        self, prefix: str, recursive: bool = False, limit: Optional[int] = None
    ) -> AsyncIterator[BucketEntry]:
        url = f"{self.BASE_URL}/b/{self._gcs_bucket_name}/o"

        params = {
            "prefix": prefix,
            "pageToken": "",
        }
        if not recursive:
            params["delimiter"] = "/"
        cnt = 0
        while True:
            async with self._request(
                "GET", url=url, params=params, headers=await self._get_auth_headers()
            ) as resp:
                data = await resp.json()
            for item in data.get("items", []):
                yield self._parse_obj(item)
                cnt += 1
                if cnt == limit:
                    return
            for prefix in data.get("prefixes", []):
                yield BlobCommonPrefix(
                    bucket=self.bucket,
                    key=prefix,
                    size=0,
                )
                cnt += 1
                if cnt == limit:
                    return
            params["pageToken"] = data.get("nextPageToken", "")
            if not params["pageToken"]:
                break

    async def head_blob(self, key: str) -> BucketEntry:
        key = urllib.parse.quote(key, safe="")
        url = f"{self.BASE_URL}/b/{self._gcs_bucket_name}/o/{key}"

        try:
            async with self._request(
                "GET", url=url, headers=await self._get_auth_headers()
            ) as resp:
                return self._parse_obj(await resp.json())
        except ResourceNotFound:
            raise ResourceNotFound(
                f"There is no object with key {key} in bucket {self.bucket.name}"
            )

    async def put_blob(
        self, key: str, body: Union[AsyncIterator[bytes], bytes]
    ) -> None:
        # Step 1: initiate multipart upload
        url = f"{self.UPLOAD_BASE_URL}/b/{self._gcs_bucket_name}/o"
        params = {"uploadType": "resumable", "name": key}
        async with self._request(
            "POST",
            url=url,
            params=params,
            headers=await self._get_auth_headers(),
            json={},
        ) as resp:
            session_url = URL(resp.headers["Location"])

        uploaded_bytes = 0
        buffer = b""

        async def _upload_chunk(*, final: bool = False) -> None:
            nonlocal uploaded_bytes
            nonlocal buffer
            size = len(buffer)
            if final:
                total = str(uploaded_bytes + size)
            else:
                total = "*"
            if size == 0:
                data_range = "*"
            else:
                data_range = f"{uploaded_bytes}-{uploaded_bytes+size-1}"
            async with self._request(
                "PUT",
                url=session_url,
                data=BytesIO(buffer),
                headers={"Content-Range": (f"bytes {data_range}/{total}")},
            ):
                pass
            uploaded_bytes += size
            buffer = b""

        if isinstance(body, bytes):
            buffer = body
        else:
            async for chunk in body:
                buffer += chunk
                if len(buffer) > self.MIN_CHUNK_SIZE:
                    await _upload_chunk()

        # Complete file:
        await _upload_chunk(final=True)

    @asyncgeneratorcontextmanager
    async def fetch_blob(self, key: str, offset: int = 0) -> AsyncIterator[bytes]:
        key = urllib.parse.quote(key, safe="")
        url = f"{self.BASE_URL}/b/{self._gcs_bucket_name}/o/{key}"
        params = {"alt": "media"}
        headers = dict(await self._get_auth_headers())
        if offset:
            headers["Range"] = f"bytes={offset}-"
        try:
            async with self._request(
                "GET", url=url, params=params, headers=headers
            ) as resp:
                async for data in resp.content.iter_any():
                    yield data
        except ResourceNotFound:
            raise ResourceNotFound(
                f"There is no object with key {key} in bucket {self.bucket.name}"
            )

    async def delete_blob(self, key: str) -> None:
        key = urllib.parse.quote(key, safe="")
        url = f"{self.BASE_URL}/b/{self._gcs_bucket_name}/o/{key}"
        try:
            async with self._request(
                "DELETE", url=url, headers=await self._get_auth_headers()
            ):
                pass
        except ResourceNotFound:
            raise ResourceNotFound(
                f"There is no object with key {key} in bucket {self.bucket.name}"
            )


@dataclass(frozen=True)
class Bucket:
    id: str
    owner: str
    cluster_name: str
    provider: "Bucket.Provider"
    created_at: datetime
    imported: bool
    public: bool = False
    name: Optional[str] = None

    @property
    def uri(self) -> URL:
        return URL(f"blob://{self.cluster_name}/{self.owner}/{self.name or self.id}")

    class Provider(str, enum.Enum):
        AWS = "aws"
        MINIO = "minio"
        AZURE = "azure"
        GCP = "gcp"
        OPEN_STACK = "open_stack"


@dataclass(frozen=True)
class BucketUsage:
    total_bytes: int
    object_count: int


@dataclass(frozen=True)
class BucketCredentials:
    bucket_id: str
    provider: "Bucket.Provider"
    credentials: Mapping[str, str]


@dataclass(frozen=True)
class PersistentBucketCredentials:
    id: str
    owner: str
    cluster_name: str
    name: Optional[str]
    read_only: bool
    credentials: List[BucketCredentials]


class Buckets(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: Config, parser: Parser) -> None:
        self._core = core
        self._config = config
        self._parser = parser

    def _parse_bucket_payload(self, payload: Mapping[str, Any]) -> Bucket:
        return Bucket(
            id=payload["id"],
            owner=payload["owner"],
            name=payload.get("name"),
            created_at=isoparse(payload["created_at"]),
            provider=Bucket.Provider(payload["provider"]),
            imported=payload.get("imported", False),
            public=payload.get("public", False),
            cluster_name=self._config.cluster_name,
        )

    def _parse_bucket_credentials_payload(
        self, payload: Mapping[str, Any]
    ) -> BucketCredentials:
        return BucketCredentials(
            bucket_id=payload["bucket_id"],
            provider=Bucket.Provider(payload["provider"]),
            credentials=payload["credentials"],
        )

    def _get_buckets_url(self, cluster_name: Optional[str]) -> URL:
        if cluster_name is None:
            cluster_name = self._config.cluster_name
        return self._config.get_cluster(cluster_name).buckets_url / "buckets"

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

    async def import_external(
        self,
        provider: Bucket.Provider,
        provider_bucket_name: str,
        credentials: Mapping[str, str],
        name: Optional[str] = None,
        cluster_name: Optional[str] = None,
    ) -> Bucket:
        url = self._get_buckets_url(cluster_name) / "import" / "external"
        auth = await self._config._api_auth()
        data = {
            "name": name,
            "provider": provider.value,
            "provider_bucket_name": provider_bucket_name,
            "credentials": credentials,
        }
        async with self._core.request("POST", url, auth=auth, json=data) as resp:
            payload = await resp.json()
            return self._parse_bucket_payload(payload)

    async def get(
        self,
        bucket_id_or_name: str,
        cluster_name: Optional[str] = None,
        bucket_owner: Optional[str] = None,
    ) -> Bucket:
        url = self._get_buckets_url(cluster_name) / bucket_id_or_name
        query = {"owner": bucket_owner} if bucket_owner else {}
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth, params=query) as resp:
            payload = await resp.json()
            return self._parse_bucket_payload(payload)

    async def rm(
        self,
        bucket_id_or_name: str,
        cluster_name: Optional[str] = None,
        bucket_owner: Optional[str] = None,
    ) -> None:
        url = self._get_buckets_url(cluster_name) / bucket_id_or_name
        query = {"owner": bucket_owner} if bucket_owner else {}
        auth = await self._config._api_auth()
        async with self._core.request("DELETE", url, auth=auth, params=query):
            pass

    async def set_public_access(
        self,
        bucket_id_or_name: str,
        public_access: bool,
        cluster_name: Optional[str] = None,
        bucket_owner: Optional[str] = None,
    ) -> Bucket:
        url = self._get_buckets_url(cluster_name) / bucket_id_or_name
        auth = await self._config._api_auth()
        data = {
            "public": public_access,
        }
        query = {"owner": bucket_owner} if bucket_owner else {}
        async with self._core.request(
            "PATCH", url, auth=auth, json=data, params=query
        ) as resp:
            payload = await resp.json()
            return self._parse_bucket_payload(payload)

    async def request_tmp_credentials(
        self,
        bucket_id_or_name: str,
        cluster_name: Optional[str] = None,
        bucket_owner: Optional[str] = None,
    ) -> BucketCredentials:
        url = (
            self._get_buckets_url(cluster_name)
            / bucket_id_or_name
            / "make_tmp_credentials"
        )
        auth = await self._config._api_auth()
        query = {"owner": bucket_owner} if bucket_owner else {}
        async with self._core.request("POST", url, auth=auth, params=query) as resp:
            payload = await resp.json()
            return self._parse_bucket_credentials_payload(payload)

    @asyncgeneratorcontextmanager
    async def get_disk_usage(
        self,
        bucket_id_or_name: str,
        cluster_name: Optional[str] = None,
        bucket_owner: Optional[str] = None,
    ) -> AsyncIterator[BucketUsage]:
        total_bytes = 0
        obj_count = 0
        async with self._get_provider(
            bucket_id_or_name, cluster_name, bucket_owner
        ) as provider:
            async with provider.list_blobs("", recursive=True) as it:
                async for obj in it:
                    total_bytes += obj.size
                    obj_count += 1
                    yield BucketUsage(total_bytes, obj_count)

    # Helper functions

    @asynccontextmanager
    async def _get_provider(
        self,
        bucket_id_or_name: str,
        cluster_name: Optional[str] = None,
        bucket_owner: Optional[str] = None,
    ) -> AsyncIterator[BucketProvider]:
        bucket = await self.get(
            bucket_id_or_name, cluster_name=cluster_name, bucket_owner=bucket_owner
        )

        async def _get_new_credentials() -> BucketCredentials:
            return await self.request_tmp_credentials(bucket.id, cluster_name)

        provider: BucketProvider
        if bucket.provider in (
            Bucket.Provider.AWS,
            Bucket.Provider.MINIO,
            Bucket.Provider.OPEN_STACK,
        ):
            async with S3Provider.create(bucket, _get_new_credentials) as provider:
                yield provider
        elif bucket.provider == Bucket.Provider.AZURE:
            async with AzureProvider.create(bucket, _get_new_credentials) as provider:
                yield provider
        elif bucket.provider == Bucket.Provider.GCP:
            async with GCSProvider.create(bucket, _get_new_credentials) as provider:
                yield provider
        else:
            assert False, f"Unknown provider {bucket.provider}"

    @asynccontextmanager
    async def _get_bucket_fs(
        self,
        bucket_name: str,
        cluster_name: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> AsyncIterator[FileSystem[PurePosixPath]]:
        async with self._get_provider(bucket_name, cluster_name, owner) as provider:
            yield BucketFS(provider)

    # Low level operations

    async def head_blob(
        self,
        bucket_id_or_name: str,
        key: str,
        cluster_name: Optional[str] = None,
        bucket_owner: Optional[str] = None,
    ) -> BucketEntry:
        async with self._get_provider(
            bucket_id_or_name, cluster_name, bucket_owner
        ) as provider:
            return await provider.head_blob(key)

    async def put_blob(
        self,
        bucket_id_or_name: str,
        key: str,
        body: Union[AsyncIterator[bytes], bytes],
        cluster_name: Optional[str] = None,
        bucket_owner: Optional[str] = None,
    ) -> None:
        async with self._get_provider(
            bucket_id_or_name, cluster_name, bucket_owner
        ) as provider:
            await provider.put_blob(key, body)

    @asyncgeneratorcontextmanager
    async def fetch_blob(
        self,
        bucket_id_or_name: str,
        key: str,
        offset: int = 0,
        cluster_name: Optional[str] = None,
        bucket_owner: Optional[str] = None,
    ) -> AsyncIterator[bytes]:
        async with self._get_provider(
            bucket_id_or_name, cluster_name, bucket_owner
        ) as provider:
            async with provider.fetch_blob(key, offset=offset) as it:
                async for chunk in it:
                    yield chunk

    async def delete_blob(
        self,
        bucket_id_or_name: str,
        key: str,
        cluster_name: Optional[str] = None,
        bucket_owner: Optional[str] = None,
    ) -> None:
        async with self._get_provider(
            bucket_id_or_name, cluster_name, bucket_owner
        ) as provider:
            return await provider.delete_blob(key)

    # Listing operations

    @asyncgeneratorcontextmanager
    async def list_blobs(
        self,
        uri: URL,
        recursive: bool = False,
        limit: Optional[int] = None,
    ) -> AsyncIterator[BucketEntry]:
        res = self._parser.split_blob_uri(uri)
        async with self._get_provider(
            res.bucket_name, res.cluster_name, res.owner
        ) as provider:
            async with provider.list_blobs(
                res.key, recursive=recursive, limit=limit
            ) as it:
                async for entry in it:
                    yield entry

    @asyncgeneratorcontextmanager
    async def glob_blobs(self, uri: URL) -> AsyncIterator[BucketEntry]:
        res = self._parser.split_blob_uri(uri)
        if _has_magic(res.bucket_name):
            raise ValueError(
                "You can not glob on bucket names. Please provide name explicitly."
            )

        async with self._get_provider(
            res.bucket_name, res.cluster_name, res.owner
        ) as provider:
            async with self._glob_blobs("", res.key, provider) as it:
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
        res = self._parser.split_blob_uri(dst)
        async with self._get_bucket_fs(
            res.bucket_name, res.cluster_name, res.owner
        ) as bucket_fs:
            transferer = FileTransferer(LocalFS(), bucket_fs)
            await transferer.transfer_file(
                src=_extract_path(src),
                dst=PurePosixPath(res.key),
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
        res = self._parser.split_blob_uri(src)
        dst = normalize_local_path_uri(dst)
        async with self._get_bucket_fs(
            res.bucket_name, res.cluster_name, res.owner
        ) as bucket_fs:
            transferer = FileTransferer(bucket_fs, LocalFS())
            await transferer.transfer_file(
                src=PurePosixPath(res.key),
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
        res = self._parser.split_blob_uri(dst)
        async with self._get_bucket_fs(
            res.bucket_name, res.cluster_name, res.owner
        ) as bucket_fs:
            transferer = FileTransferer(LocalFS(), bucket_fs)
            await transferer.transfer_dir(
                src=_extract_path(src),
                dst=PurePosixPath(res.key),
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
        res = self._parser.split_blob_uri(src)
        dst = normalize_local_path_uri(dst)
        async with self._get_bucket_fs(
            res.bucket_name, res.cluster_name, res.owner
        ) as bucket_fs:
            transferer = FileTransferer(bucket_fs, LocalFS())
            await transferer.transfer_dir(
                src=PurePosixPath(res.key),
                dst=_extract_path(dst),
                update=update,
                continue_=continue_,
                filter=filter,
                progress=progress,
            )

    async def blob_is_dir(self, uri: URL) -> bool:
        res = self._parser.split_blob_uri(uri)
        if res.key.endswith("/"):
            return True
        async with self._get_bucket_fs(
            res.bucket_name, res.cluster_name, res.owner
        ) as bucket_fs:
            return await bucket_fs.is_dir(PurePosixPath(res.key))

    async def blob_rm(
        self,
        uri: URL,
        *,
        recursive: bool = False,
        progress: Optional[AbstractDeleteProgress] = None,
    ) -> None:
        res = self._parser.split_blob_uri(uri)
        async with self._get_bucket_fs(
            res.bucket_name, res.cluster_name, res.owner
        ) as bucket_fs:
            await file_utils.rm(bucket_fs, PurePosixPath(res.key), recursive, progress)

    async def make_signed_url(
        self,
        uri: URL,
        expires_in_seconds: int = 3600,
    ) -> URL:
        res = self._parser.split_blob_uri(uri)
        url = (
            self._get_buckets_url(res.cluster_name) / res.bucket_name / "sign_blob_url"
        )
        auth = await self._config._api_auth()
        data = {
            "key": res.key,
            "expires_in_sec": expires_in_seconds,
        }
        async with self._core.request(
            "POST", url, auth=auth, json=data, params={"owner": res.owner}
        ) as resp:
            resp_data = await resp.json()
            return URL(resp_data["url"])

    # Persistent bucket credentials commands

    def _parse_persistent_credentials_payload(
        self, payload: Mapping[str, Any]
    ) -> PersistentBucketCredentials:
        return PersistentBucketCredentials(
            id=payload["id"],
            owner=payload["owner"],
            name=payload.get("name"),
            cluster_name=self._config.cluster_name,
            credentials=[
                self._parse_bucket_credentials_payload(item)
                for item in payload["credentials"]
            ],
            read_only=payload.get("read_only", False),
        )

    def _get_persistent_credentials_url(self, cluster_name: Optional[str]) -> URL:
        if cluster_name is None:
            cluster_name = self._config.cluster_name
        return (
            self._config.get_cluster(cluster_name).buckets_url
            / "persistent_credentials"
        )

    @asyncgeneratorcontextmanager
    async def persistent_credentials_list(
        self, cluster_name: Optional[str] = None
    ) -> AsyncIterator[PersistentBucketCredentials]:
        url = self._get_persistent_credentials_url(cluster_name)
        auth = await self._config._api_auth()
        headers = {"Accept": "application/x-ndjson"}
        async with self._core.request("GET", url, headers=headers, auth=auth) as resp:
            if resp.headers.get("Content-Type", "").startswith("application/x-ndjson"):
                async for line in resp.content:
                    server_message = json.loads(line)
                    if "error" in server_message:
                        raise NDJSONError(server_message["error"])
                    yield self._parse_persistent_credentials_payload(server_message)
            else:
                ret = await resp.json()
                for cred_data in ret:
                    yield self._parse_persistent_credentials_payload(cred_data)

    async def persistent_credentials_create(
        self,
        bucket_ids: Iterable[str],
        name: Optional[str] = None,
        cluster_name: Optional[str] = None,
        read_only: Optional[bool] = False,
    ) -> PersistentBucketCredentials:
        url = self._get_persistent_credentials_url(cluster_name)
        auth = await self._config._api_auth()
        data = {
            "name": name,
            "bucket_ids": list(bucket_ids),
            "read_only": read_only,
        }
        async with self._core.request("POST", url, auth=auth, json=data) as resp:
            payload = await resp.json()
            return self._parse_persistent_credentials_payload(payload)

    async def persistent_credentials_get(
        self, credential_id_or_name: str, cluster_name: Optional[str] = None
    ) -> PersistentBucketCredentials:
        url = self._get_persistent_credentials_url(cluster_name) / credential_id_or_name
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            payload = await resp.json()
            return self._parse_persistent_credentials_payload(payload)

    async def persistent_credentials_rm(
        self, credential_id_or_name: str, cluster_name: Optional[str] = None
    ) -> None:
        url = self._get_persistent_credentials_url(cluster_name) / credential_id_or_name
        auth = await self._config._api_auth()
        async with self._core.request("DELETE", url, auth=auth):
            pass
