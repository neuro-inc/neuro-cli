from pathlib import Path
from typing import Awaitable, Callable, List, Optional

import aiohttp
from yarl import URL

from ._abc import (
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
from ._admin import (
    _Admin,
    _Balance,
    _CloudProvider,
    _Cluster,
    _ClusterUser,
    _ClusterUserRoleType,
    _ClusterUserWithInfo,
    _ConfigCluster,
    _NodePool,
    _Org,
    _OrgCluster,
    _OrgUser,
    _OrgUserRoleType,
    _OrgUserWithInfo,
    _Quota,
    _Storage,
    _UserInfo,
)
from ._bucket_base import (
    BlobCommonPrefix,
    BlobObject,
    Bucket,
    BucketCredentials,
    BucketEntry,
    PersistentBucketCredentials,
)
from ._buckets import Buckets
from ._client import Client, Preset
from ._config import Config
from ._config_factory import (
    CONFIG_ENV_NAME,
    DEFAULT_API_URL,
    DEFAULT_CONFIG_PATH,
    PASS_CONFIG_ENV_NAME,
    Factory,
)
from ._core import DEFAULT_TIMEOUT
from ._disks import Disk, Disks
from ._errors import (
    AuthenticationError,
    AuthError,
    AuthorizationError,
    ClientError,
    ConfigError,
    IllegalArgumentError,
    NDJSONError,
    NotSupportedError,
    ResourceNotFound,
    ServerNotAvailable,
    StdStreamError,
)
from ._file_filter import AsyncFilterFunc, FileFilter
from ._images import Images
from ._jobs import (
    Container,
    HTTPPort,
    JobDescription,
    JobRestartPolicy,
    Jobs,
    JobStatus,
    JobStatusHistory,
    JobStatusItem,
    JobTelemetry,
    Resources,
    StdStream,
)
from ._parser import (
    DiskVolume,
    EnvParseResult,
    Parser,
    SecretFile,
    Volume,
    VolumeParseResult,
)
from ._parsing_utils import LocalImage, RemoteImage, Tag, TagOption
from ._plugins import ConfigBuilder, ConfigScope, PluginManager, VersionChecker
from ._secrets import Secret, Secrets
from ._server_cfg import Cluster
from ._service_accounts import ServiceAccount, ServiceAccounts
from ._storage import DiskUsageInfo, FileStatus, FileStatusType, Storage
from ._tracing import gen_trace_id
from ._url_utils import CLUSTER_SCHEMES as SCHEMES
from ._users import Action, Permission, Quota, Share, Users
from ._utils import _ContextManager, find_project_root

__version__ = "21.11.4"


__all__ = (
    "AbstractDeleteProgress",
    "AbstractDockerImageProgress",
    "AbstractFileProgress",
    "AbstractRecursiveFileProgress",
    "Action",
    "AsyncFilterFunc",
    "AuthError",
    "AuthError",
    "AuthenticationError",
    "AuthorizationError",
    "BlobCommonPrefix",
    "BlobObject",
    "Bucket",
    "BucketCredentials",
    "BucketEntry",
    "Buckets",
    "CONFIG_ENV_NAME",
    "Client",
    "ClientError",
    "Cluster",
    "Config",
    "ConfigBuilder",
    "ConfigError",
    "ConfigScope",
    "Container",
    "DEFAULT_API_URL",
    "DEFAULT_CONFIG_PATH",
    "Disk",
    "DiskUsageInfo",
    "DiskVolume",
    "Disks",
    "EnvParseResult",
    "Factory",
    "FileFilter",
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
    "JobStatusItem",
    "JobTelemetry",
    "Jobs",
    "LocalImage",
    "NDJSONError",
    "NotSupportedError",
    "PASS_CONFIG_ENV_NAME",
    "Parser",
    "Permission",
    "PersistentBucketCredentials",
    "PluginManager",
    "Preset",
    "Quota",
    "RemoteImage",
    "ResourceNotFound",
    "Resources",
    "SCHEMES",
    "Secret",
    "SecretFile",
    "Secrets",
    "ServerNotAvailable",
    "ServiceAccount",
    "ServiceAccounts",
    "Share",
    "StdStream",
    "StdStreamError",
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
    "VersionChecker",
    "Volume",
    "VolumeParseResult",
    "_Admin",
    "_Balance",
    "_CloudProvider",
    "_Cluster",
    "_ClusterUser",
    "_ClusterUserRoleType",
    "_ClusterUserWithInfo",
    "_ConfigCluster",
    "_NodePool",
    "_Org",
    "_OrgCluster",
    "_OrgUser",
    "_OrgUserRoleType",
    "_OrgUserWithInfo",
    "_Quota",
    "_Storage",
    "_UserInfo",
    "__version__",
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
