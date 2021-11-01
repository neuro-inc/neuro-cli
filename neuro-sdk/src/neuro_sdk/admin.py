from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum, unique
from typing import Any, Dict, List, Mapping, Optional

from dateutil.parser import isoparse
from yarl import URL

from .config import Config
from .core import _Core
from .errors import NotSupportedError
from .server_cfg import Preset
from .utils import NoPublicConstructor


@unique
class _ClusterUserRoleType(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class _UserInfo:
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: Optional[datetime]

    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        if self.last_name:
            return self.last_name
        return ""


@dataclass(frozen=True)
class _Quota:
    total_running_jobs: Optional[int] = None


@dataclass(frozen=True)
class _Balance:
    credits: Optional[Decimal] = None
    spent_credits: Decimal = Decimal("0")


@dataclass(frozen=True)
class _ClusterUser:
    user_name: str
    role: _ClusterUserRoleType
    quota: _Quota
    user_info: _UserInfo
    balance: _Balance


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


@dataclass(frozen=True)
class _Storage:
    description: str


@dataclass(frozen=True)
class _CloudProvider:
    type: str
    region: Optional[str]
    zones: List[str]
    node_pools: List[_NodePool]
    storage: Optional[_Storage]


@dataclass(frozen=True)
class _Cluster:
    name: str
    status: str
    cloud_provider: Optional[_CloudProvider] = None


class _Admin(metaclass=NoPublicConstructor):
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

    async def list_cloud_providers(self) -> Dict[str, Dict[str, Any]]:
        url = self._config.api_url / "cloud_providers"
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            return await resp.json()

    async def list_clusters(self) -> Dict[str, _Cluster]:
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

    async def add_cluster(self, name: str, config: Dict[str, Any]) -> None:
        url = self._admin_url / "clusters"
        auth = await self._config._api_auth()
        payload = {"name": name}
        async with self._core.request("POST", url, auth=auth, json=payload) as resp:
            resp
        url = self._config.api_url / "clusters" / name / "cloud_provider"
        url = url.with_query(start_deployment="true")
        async with self._core.request("PUT", url, auth=auth, json=config) as resp:
            resp

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

    async def list_cluster_users(
        self, cluster_name: Optional[str] = None
    ) -> List[_ClusterUser]:
        cluster_name = cluster_name or self._config.cluster_name
        url = self._admin_url / "clusters" / cluster_name / "users"
        auth = await self._config._api_auth()
        async with self._core.request(
            "GET", url, auth=auth, params={"with_user_info": "true"}
        ) as resp:
            res = await resp.json()
            return [_cluster_user_from_api(payload) for payload in res]

    async def get_cluster_user(
        self,
        cluster_name: Optional[str] = None,
        user_name: Optional[str] = None,
    ) -> _ClusterUser:
        cluster_name = cluster_name or self._config.cluster_name
        user_name = user_name or self._config.username
        url = self._admin_url / "clusters" / cluster_name / "users" / user_name
        auth = await self._config._api_auth()
        async with self._core.request(
            "GET", url, auth=auth, params={"with_user_info": "true"}
        ) as resp:
            res = await resp.json()
            return _cluster_user_from_api(res)

    async def add_cluster_user(
        self, cluster_name: str, user_name: str, role: str
    ) -> _ClusterUser:
        url = self._admin_url / "clusters" / cluster_name / "users"
        payload = {"user_name": user_name, "role": role}
        auth = await self._config._api_auth()

        async with self._core.request(
            "POST", url, json=payload, auth=auth, params={"with_user_info": "true"}
        ) as resp:
            payload = await resp.json()
            return _cluster_user_from_api(payload)

    async def remove_cluster_user(self, cluster_name: str, user_name: str) -> None:
        url = self._admin_url / "clusters" / cluster_name / "users" / user_name
        auth = await self._config._api_auth()

        async with self._core.request("DELETE", url, auth=auth):
            # No content response
            pass

    async def set_user_quota(
        self,
        cluster_name: str,
        user_name: str,
        total_running_jobs: Optional[int],
    ) -> _ClusterUser:
        url = (
            self._admin_url / "clusters" / cluster_name / "users" / user_name / "quota"
        )
        payload = {
            "quota": {
                "total_running_jobs": total_running_jobs,
            },
        }
        payload["quota"] = {k: v for k, v in payload["quota"].items() if v is not None}

        auth = await self._config._api_auth()

        async with self._core.request(
            "PATCH", url, json=payload, auth=auth, params={"with_user_info": "true"}
        ) as resp:
            payload = await resp.json()
            return _cluster_user_from_api(payload)

    async def set_user_credits(
        self,
        cluster_name: str,
        user_name: str,
        credits: Optional[Decimal],
    ) -> _ClusterUser:
        url = (
            self._admin_url
            / "clusters"
            / cluster_name
            / "users"
            / user_name
            / "balance"
        )
        payload = {
            "credits": str(credits) if credits is not None else None,
        }

        auth = await self._config._api_auth()

        async with self._core.request(
            "PATCH", url, json=payload, auth=auth, params={"with_user_info": "true"}
        ) as resp:
            payload = await resp.json()
            return _cluster_user_from_api(payload)

    async def add_user_credits(
        self,
        cluster_name: str,
        user_name: str,
        additional_credits: Decimal,
    ) -> _ClusterUser:
        url = (
            self._admin_url
            / "clusters"
            / cluster_name
            / "users"
            / user_name
            / "balance"
        )
        payload = {"additional_credits": str(additional_credits)}
        auth = await self._config._api_auth()

        async with self._core.request(
            "PATCH", url, json=payload, auth=auth, params={"with_user_info": "true"}
        ) as resp:
            payload = await resp.json()
            return _cluster_user_from_api(payload)

    async def get_cloud_provider_options(
        self, cloud_provider_name: str
    ) -> Mapping[str, Any]:
        url = self._config.api_url / "cloud_providers" / cloud_provider_name
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            return await resp.json()


def _user_info_from_api(payload: Dict[str, Any]) -> _UserInfo:
    created_at = payload.get("created_at")
    if created_at is not None:
        created_at = isoparse(created_at)
    return _UserInfo(
        email=payload["email"],
        first_name=payload.get("first_name"),
        last_name=payload.get("last_name"),
        created_at=created_at,
    )


def _cluster_user_from_api(payload: Dict[str, Any]) -> _ClusterUser:
    quota_dict = payload.get("quota", {})
    balance_dict = payload.get("balance", {})
    return _ClusterUser(
        user_name=payload["user_name"],
        role=_ClusterUserRoleType(payload["role"]),
        quota=_Quota(
            total_running_jobs=quota_dict.get("total_running_jobs"),
        ),
        balance=_Balance(
            credits=Decimal(balance_dict["credits"])
            if "credits" in balance_dict
            else None,
            spent_credits=Decimal(balance_dict["spent_credits"]),
        ),
        user_info=_user_info_from_api(payload["user_info"]),
    )


def _cluster_from_api(payload: Dict[str, Any]) -> _Cluster:
    if "cloud_provider" in payload:
        cloud_provider = payload["cloud_provider"]
        return _Cluster(
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
    return _Cluster(name=payload["name"], status=payload["status"])


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
