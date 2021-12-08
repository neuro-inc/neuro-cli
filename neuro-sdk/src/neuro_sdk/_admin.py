# Admin API is experimental,
# remove underscore prefix after stabilizing and making public

from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Mapping, Optional

import aiohttp
from neuro_admin_client import AdminClientBase
from neuro_admin_client import Balance as _Balance
from neuro_admin_client import Cluster as _Cluster
from neuro_admin_client import ClusterUser as _ClusterUser
from neuro_admin_client import ClusterUserRoleType as _ClusterUserRoleType
from neuro_admin_client import ClusterUserWithInfo as _ClusterUserWithInfo
from neuro_admin_client import Org as _Org
from neuro_admin_client import OrgCluster as _OrgCluster
from neuro_admin_client import OrgUser as _OrgUser
from neuro_admin_client import OrgUserRoleType as _OrgUserRoleType
from neuro_admin_client import OrgUserWithInfo as _OrgUserWithInfo
from neuro_admin_client import Quota as _Quota
from neuro_admin_client import UserInfo as _UserInfo
from prompt_toolkit.eventloop.async_context_manager import asynccontextmanager
from yarl import URL

from ._config import Config
from ._core import _Core
from ._errors import NotSupportedError
from ._rewrite import rewrite_module
from ._server_cfg import Preset
from ._utils import NoPublicConstructor

# Explicit __all__ to re-export neuro_admin_client entities

__all__ = [
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
]


@rewrite_module
@dataclass(frozen=True)
class _NodePool:
    min_size: int
    max_size: int
    machine_type: str
    available_cpu: float
    available_memory_mb: int
    disk_size_gb: int
    disk_type: Optional[str] = None
    gpu: int = 0
    gpu_model: Optional[str] = None
    is_tpu_enabled: bool = False
    is_preemptible: bool = False
    idle_size: int = 0


@rewrite_module
@dataclass(frozen=True)
class _Storage:
    description: str


@rewrite_module
@dataclass(frozen=True)
class _CloudProvider:
    type: str
    region: Optional[str]
    zones: List[str]
    node_pools: List[_NodePool]
    storage: Optional[_Storage]


@rewrite_module
@dataclass(frozen=True)
class _ConfigCluster:
    name: str
    status: str
    cloud_provider: Optional[_CloudProvider] = None


@rewrite_module
class _Admin(AdminClientBase, metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: Config) -> None:
        self._core = core
        self._config = config

    @property
    def _admin_url(self) -> URL:
        url = self._config.admin_url
        if not url:
            raise NotSupportedError("admin API is not supported by server")
        else:
            return url

    @asynccontextmanager
    async def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Mapping[str, str]] = None,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        url = self._admin_url / path
        auth = await self._config._api_auth()
        async with self._core.request(
            method=method,
            url=url,
            params=params,
            json=json,
            auth=auth,
        ) as resp:
            yield resp

    async def list_cloud_providers(self) -> Dict[str, Dict[str, Any]]:
        url = self._config.api_url / "cloud_providers"
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            return await resp.json()

    async def list_config_clusters(self) -> Dict[str, _ConfigCluster]:
        url = (self._config.api_url / "clusters").with_query(
            include="cloud_provider_infra"
        )
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            payload = await resp.json()
            ret = {}
            for item in payload:
                cluster = _cluster_from_api(item)
                ret[cluster.name] = cluster
            return ret

    async def setup_cluster_cloud_provider(
        self, name: str, config: Dict[str, Any]
    ) -> None:
        auth = await self._config._api_auth()
        url = self._config.api_url / "clusters" / name / "cloud_provider"
        url = url.with_query(start_deployment="true")
        async with self._core.request("PUT", url, auth=auth, json=config):
            pass

    async def update_cluster_resource_presets(
        self, name: str, presets: Mapping[str, Preset]
    ) -> None:
        url = self._config.api_url / "clusters" / name / "orchestrator/resource_presets"
        auth = await self._config._api_auth()
        payload = [
            _serialize_resource_preset(name, preset) for name, preset in presets.items()
        ]
        async with self._core.request("PUT", url, auth=auth, json=payload):
            pass

    async def get_cloud_provider_options(
        self, cloud_provider_name: str
    ) -> Mapping[str, Any]:
        url = self._config.api_url / "cloud_providers" / cloud_provider_name
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            return await resp.json()


def _cluster_from_api(payload: Dict[str, Any]) -> _ConfigCluster:
    if "cloud_provider" in payload:
        cloud_provider = payload["cloud_provider"]
        return _ConfigCluster(
            name=payload["name"],
            status=payload["status"],
            cloud_provider=_CloudProvider(
                type=cloud_provider["type"],
                region=cloud_provider.get("region"),
                zones=(
                    [cloud_provider["zone"]]
                    if "zone" in cloud_provider
                    else cloud_provider.get("zones", [])
                ),
                node_pools=[
                    _node_pool_from_api(np)
                    for np in cloud_provider.get("node_pools", [])
                ],
                storage=(
                    _storage_from_api(cloud_provider["storage"])
                    if "storage" in cloud_provider
                    else None
                ),
            ),
        )
    return _ConfigCluster(name=payload["name"], status=payload["status"])


def _node_pool_from_api(payload: Dict[str, Any]) -> _NodePool:
    return _NodePool(
        min_size=payload["min_size"],
        max_size=payload["max_size"],
        idle_size=payload.get("idle_size", 0),
        machine_type=payload["machine_type"],
        available_cpu=payload["available_cpu"],
        available_memory_mb=payload["available_memory_mb"],
        disk_type=payload.get("disk_type"),
        disk_size_gb=payload["disk_size_gb"],
        gpu=payload.get("gpu", 0),
        gpu_model=payload.get("gpu_model"),
        is_tpu_enabled=payload.get("is_tpu_enabled", False),
        is_preemptible=payload.get("is_preemptible", False),
    )


def _storage_from_api(payload: Dict[str, Any]) -> _Storage:
    return _Storage(description=payload["description"])


def _serialize_resource_preset(name: str, preset: Preset) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "name": name,
        "credits_per_hour": str(preset.credits_per_hour),
        "cpu": preset.cpu,
        "memory_mb": preset.memory_mb,
        "scheduler_enabled": preset.scheduler_enabled,
        "preemptible_node": preset.preemptible_node,
    }
    if preset.gpu:
        result["gpu"] = preset.gpu
        result["gpu_model"] = preset.gpu_model
    if preset.tpu_type and preset.tpu_software_version:
        result["tpu"] = {
            "type": preset.tpu_type,
            "software_version": preset.tpu_software_version,
        }
    return result
