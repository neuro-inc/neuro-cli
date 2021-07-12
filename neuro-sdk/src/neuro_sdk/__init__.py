from pathlib import Path
from typing import Awaitable, Callable, List, Optional

import aiohttp
from yarl import URL

from .abc import (
    AbstractDeleteProgress,
    AbstractDockerImageProgress,
    AbstractFileProgress,
    AbstractRecursiveFileProgress,
    ImageCommitFinished,
    ImageCommitStarted,
    ImageProgressPull,
    ImageProgressPush,
    ImageProgressSave,
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
    PASS_CONFIG_ENV_NAME,
    Factory,
)
from .core import DEFAULT_TIMEOUT
from .disks import Disk, Disks
from .errors import (
    AuthenticationError,
    AuthError,
    AuthorizationError,
    ClientError,
    ConfigError,
    IllegalArgumentError,
    NDJSONError,
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
)
from .parser import (
    DiskVolume,
    EnvParseResult,
    Parser,
    SecretFile,
    Volume,
    VolumeParseResult,
)
from .parsing_utils import LocalImage, RemoteImage, Tag, TagOption
from .plugins import ConfigBuilder, PluginManager
from .secrets import Secret, Secrets
from .server_cfg import Cluster
from .service_accounts import ServiceAccount, ServiceAccounts
from .storage import FileStatus, FileStatusType, Storage
from .tracing import gen_trace_id
from .users import Action, Permission, Share, Users
from .utils import _ContextManager, find_project_root

__version__ = "21.7.12a1"


__all__ = (
    "AbstractDeleteProgress",
    "AbstractDockerImageProgress",
    "AbstractFileProgress",
    "AbstractRecursiveFileProgress",
    "Action",
    "AuthError",
    "AuthError",
    "AuthenticationError",
    "AuthorizationError",
    "Blob",
    "BlobListing",
    "BlobStorage",
    "BucketListing",
    "CONFIG_ENV_NAME",
    "Client",
    "ClientError",
    "Cluster",
    "Config",
    "ConfigBuilder",
    "ConfigError",
    "Container",
    "DEFAULT_API_URL",
    "DEFAULT_CONFIG_PATH",
    "Disk",
    "DiskVolume",
    "Disks",
    "EnvParseResult",
    "Factory",
    "FileStatus",
    "FileStatusType",
    "HTTPPort",
    "IllegalArgumentError",
    "ImageCommitFinished",
    "ImageCommitStarted",
    "ImageProgressPull",
    "ImageProgressPush",
    "ImageProgressSave",
    "ImageProgressStep",
    "Images",
    "JobDescription",
    "JobRestartPolicy",
    "JobStatus",
    "JobStatusHistory",
    "JobTelemetry",
    "Jobs",
    "LocalImage",
    "NDJSONError",
    "PASS_CONFIG_ENV_NAME",
    "Parser",
    "Permission",
    "PluginManager",
    "PrefixListing",
    "Preset",
    "RemoteImage",
    "ResourceNotFound",
    "Resources",
    "Secret",
    "SecretFile",
    "Secrets",
    "ServerNotAvailable",
    "ServiceAccount",
    "ServiceAccounts",
    "Share",
    "StdStream",
    "Storage",
    "StorageProgressComplete",
    "StorageProgressDelete",
    "StorageProgressEnterDir",
    "StorageProgressFail",
    "StorageProgressLeaveDir",
    "StorageProgressStart",
    "StorageProgressStep",
    "Tag",
    "TagOption",
    "Users",
    "Volume",
    "VolumeParseResult",
    "find_project_root",
    "gen_trace_id",
    "get",
    "login",
    "login_with_token",
    "logout",
)


def get(
    *,
    path: Optional[Path] = None,
    timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT,
    trace_configs: Optional[List[aiohttp.TraceConfig]] = None,
) -> _ContextManager[Client]:
    return _ContextManager[Client](_get(path, timeout, trace_configs))


async def _get(
    path: Optional[Path],
    timeout: aiohttp.ClientTimeout,
    trace_configs: Optional[List[aiohttp.TraceConfig]],
) -> Client:
    return await Factory(path, trace_configs).get(timeout=timeout)


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
