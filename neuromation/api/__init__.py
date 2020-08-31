from pathlib import Path
from typing import Awaitable, Callable, Optional

import aiohttp
from yarl import URL

from .abc import (
    AbstractDeleteProgress,
    AbstractDockerImageProgress,
    AbstractFileProgress,
    AbstractRecursiveFileProgress,
    ImageProgressPull,
    ImageProgressPush,
    ImageProgressStep,
    StorageProgressComplete,
    StorageProgressDelete,
    StorageProgressEnterDir,
    StorageProgressFail,
    StorageProgressLeaveDir,
    StorageProgressStart,
    StorageProgressStep,
)
from .blob_storage import Blob, BlobListing, BlobStorage, BucketListing, PrefixListing
from .client import Client, Preset
from .config import Config
from .config_factory import (
    CONFIG_ENV_NAME,
    DEFAULT_API_URL,
    DEFAULT_CONFIG_PATH,
    Factory,
)
from .core import DEFAULT_TIMEOUT
from .errors import (
    AuthenticationError,
    AuthError,
    AuthorizationError,
    ClientError,
    ConfigError,
    IllegalArgumentError,
    ResourceNotFound,
    ServerNotAvailable,
)
from .images import Images
from .jobs import (
    Container,
    HTTPPort,
    JobDescription,
    JobRestartPolicy,
    Jobs,
    JobStatus,
    JobStatusHistory,
    JobTelemetry,
    Resources,
    StdStream,
    Volume,
)
from .parser import Parser
from .parsing_utils import LocalImage, RemoteImage, TagOption
from .plugins import PluginManager
from .secrets import Secret, Secrets
from .server_cfg import Cluster
from .storage import FileStatus, FileStatusType, Storage
from .tracing import gen_trace_id
from .users import Action, Permission, Share, Users
from .utils import _ContextManager, find_project_root


__all__ = (
    "DEFAULT_API_URL",
    "DEFAULT_CONFIG_PATH",
    "CONFIG_ENV_NAME",
    "Jobs",
    "JobDescription",
    "JobRestartPolicy",
    "JobStatus",
    "JobStatusHistory",
    "JobTelemetry",
    "Resources",
    "StdStream",
    "Volume",
    "HTTPPort",
    "Users",
    "Action",
    "Permission",
    "Share",
    "Client",
    "Preset",
    "BlobStorage",
    "BucketListing",
    "BlobListing",
    "Blob",
    "PrefixListing",
    "Storage",
    "FileStatusType",
    "FileStatus",
    "Container",
    "ResourceNotFound",
    "ClientError",
    "IllegalArgumentError",
    "AuthError",
    "AuthenticationError",
    "AuthorizationError",
    "ServerNotAvailable",
    "AbstractFileProgress",
    "AbstractRecursiveFileProgress",
    "AbstractDeleteProgress",
    "AbstractDockerImageProgress",
    "StorageProgressStart",
    "StorageProgressComplete",
    "StorageProgressStep",
    "StorageProgressFail",
    "StorageProgressEnterDir",
    "StorageProgressLeaveDir",
    "StorageProgressDelete",
    "ImageProgressPull",
    "ImageProgressPush",
    "ImageProgressStep",
    "TagOption",
    "RemoteImage",
    "LocalImage",
    "Factory",
    "get",
    "login",
    "login_with_token",
    "logout",
    "Config",
    "ConfigError",
    "gen_trace_id",
    "Cluster",
    "Images",
    "Parser",
    "Secrets",
    "Secret",
    "PluginManager",
    "find_project_root",
)


def get(
    *, path: Optional[Path] = None, timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT
) -> _ContextManager[Client]:
    return _ContextManager[Client](_get(path, timeout))


async def _get(path: Optional[Path], timeout: aiohttp.ClientTimeout) -> Client:
    return await Factory(path).get(timeout=timeout)


async def login(
    show_browser_cb: Callable[[URL], Awaitable[None]],
    *,
    url: URL = DEFAULT_API_URL,
    path: Optional[Path] = None,
    timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT,
) -> None:
    await Factory(path).login(show_browser_cb, url=url, timeout=timeout)


async def login_with_token(
    token: str,
    *,
    url: URL = DEFAULT_API_URL,
    path: Optional[Path] = None,
    timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT,
) -> None:
    await Factory(path).login_with_token(token, url=url, timeout=timeout)


async def login_headless(
    get_auth_code_cb: Callable[[URL], Awaitable[str]],
    *,
    url: URL = DEFAULT_API_URL,
    path: Optional[Path] = None,
    timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT,
) -> None:
    await Factory(path).login_headless(get_auth_code_cb, url=url, timeout=timeout)


async def logout(
    *,
    path: Optional[Path] = None,
    show_browser_cb: Callable[[URL], Awaitable[None]] = None,
) -> None:
    await Factory(path).logout(show_browser_cb)
