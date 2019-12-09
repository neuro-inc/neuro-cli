from dataclasses import dataclass
from typing import Any, Dict, Optional

from neuromation.api.config import Config
from neuromation.api.core import _Core
from neuromation.api.utils import NoPublicConstructor


@dataclass(frozen=True)
class _QuotaInfo:
    cluster_name: str
    # All time in seconds
    cpu_time_spent: int
    cpu_time_limit: Optional[int]
    gpu_time_spent: int
    gpu_time_limit: Optional[int]

    @property
    def cpu_time_left(self) -> Optional[int]:
        return self._get_remaining_time(self.cpu_time_spent, self.cpu_time_limit)

    @property
    def gpu_time_left(self) -> Optional[int]:
        return self._get_remaining_time(self.gpu_time_spent, self.gpu_time_limit)

    def _get_remaining_time(
        self, time_spent: int, time_limit: Optional[int]
    ) -> Optional[int]:
        if time_limit is None:
            return None
        return max(time_limit - time_spent, 0)


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
        cpu_time_spent = jobs_payload["total_non_gpu_run_time_minutes"]
        gpu_time_spent = jobs_payload["total_gpu_run_time_minutes"]
        cpu_time_limit = quota_payload.get("total_non_gpu_run_time_minutes", None)
        gpu_time_limit = quota_payload.get("total_gpu_run_time_minutes", None)

        ret[cluster_name] = _QuotaInfo(
            cluster_name=cluster_name,
            cpu_time_spent=cpu_time_spent * 60,
            cpu_time_limit=cpu_time_limit * 60 if cpu_time_limit else None,
            gpu_time_spent=gpu_time_spent * 60,
            gpu_time_limit=gpu_time_limit * 60 if gpu_time_limit else None,
        )
    return ret
