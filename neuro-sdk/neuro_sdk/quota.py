from dataclasses import dataclass
from typing import Any, Dict, Optional

from .config import Config
from .core import _Core
from .utils import NoPublicConstructor


@dataclass(frozen=True)
class _QuotaInfo:
    cluster_name: str
    cpu_time_spent: float
    cpu_time_limit: float
    gpu_time_spent: float
    gpu_time_limit: float

    @property
    def cpu_time_left(self) -> float:
        return self._get_remaining_time(self.cpu_time_spent, self.cpu_time_limit)

    @property
    def gpu_time_left(self) -> float:
        return self._get_remaining_time(self.gpu_time_spent, self.gpu_time_limit)

    def _get_remaining_time(self, time_spent: float, time_limit: float) -> float:
        if time_limit > time_spent:
            return time_limit - time_spent
        return 0.0


class _Quota(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: Config) -> None:
        self._core = core
        self._config = config

    async def get(self, user: Optional[str] = None) -> Dict[str, _QuotaInfo]:
        user = user or self._config.username
        url = self._config.api_url / "stats" / "users" / user
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            res = await resp.json()
            return _quota_info_from_api(res)


def _quota_info_from_api(payload: Dict[str, Any]) -> Dict[str, _QuotaInfo]:
    clusters = payload["clusters"]
    ret: Dict[str, _QuotaInfo] = {}
    for cluster_payload in clusters:
        cluster_name = cluster_payload["name"]
        jobs_payload = cluster_payload["jobs"]
        quota_payload = cluster_payload.get("quota", {})
        ret[cluster_name] = _QuotaInfo(
            cluster_name=cluster_name,
            cpu_time_spent=float(
                int(jobs_payload["total_non_gpu_run_time_minutes"]) * 60
            ),
            cpu_time_limit=float(
                quota_payload.get("total_non_gpu_run_time_minutes", "inf")
            )
            * 60,
            gpu_time_spent=float(int(jobs_payload["total_gpu_run_time_minutes"]) * 60),
            gpu_time_limit=float(quota_payload.get("total_gpu_run_time_minutes", "inf"))
            * 60,
        )
    return ret
