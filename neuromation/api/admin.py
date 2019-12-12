from dataclasses import dataclass
from enum import Enum, unique
from typing import Any, Dict, List, Optional

from neuromation.api.config import Config
from neuromation.api.core import _Core
from neuromation.api.utils import NoPublicConstructor


@unique
class _ClusterUserRoleType(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class _ClusterUser:
    user_name: str
    role: _ClusterUserRoleType


@dataclass(frozen=True)
class _Cluster:
    name: str


class _Admin(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: Config) -> None:
        self._core = core
        self._config = config

    async def list_cluster_users(
        self, cluster_name: Optional[str] = None
    ) -> List[_ClusterUser]:
        cluster_name = cluster_name or self._config.cluster_name
        url = self._config.admin_url / "clusters" / cluster_name / "users"
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            res = await resp.json()
            return [_cluster_user_from_api(payload) for payload in res]

    async def list_clusters(self,) -> Dict[str, _Cluster]:
        url = self._config.admin_url / "clusters"
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            payload = await resp.json()
            ret = {}
            for item in payload:
                cluster = _cluster_from_api(item)
                ret[cluster.name] = cluster
            return ret


def _cluster_user_from_api(payload: Dict[str, Any]) -> _ClusterUser:
    return _ClusterUser(
        user_name=payload["user_name"], role=_ClusterUserRoleType(payload["role"])
    )


def _cluster_from_api(payload: Dict[str, Any]) -> _Cluster:
    return _Cluster(name=payload["name"])
