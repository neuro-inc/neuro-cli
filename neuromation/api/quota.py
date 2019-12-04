from dataclasses import dataclass
from typing import Any, Dict, Optional

from yarl import URL

from neuromation.api.config import _Config
from neuromation.api.core import _Core
from neuromation.api.utils import NoPublicConstructor


@dataclass(frozen=True)
class _QuotaInfo:
    name: str
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
    def __init__(self, core: _Core, config: _Config) -> None:
        self._core = core
        self._config = config

    async def get(self, user: Optional[str] = None) -> _QuotaInfo:
        user = user or self._config.auth_token.username
        url = URL(f"stats/users/{user}")
        async with self._core.request("GET", url) as resp:
            res = await resp.json()
            return _quota_info_from_api(res)


def _quota_info_from_api(payload: Dict[str, Any]) -> _QuotaInfo:
    jobs = payload["jobs"]
    spent_gpu = float(int(jobs["total_gpu_run_time_minutes"]) * 60)
    spent_cpu = float(int(jobs["total_non_gpu_run_time_minutes"]) * 60)
    quota = payload["quota"]
    limit_gpu = float(quota.get("total_gpu_run_time_minutes", "inf")) * 60
    limit_cpu = float(quota.get("total_non_gpu_run_time_minutes", "inf")) * 60
    return _QuotaInfo(
        name=payload["name"],
        gpu_time_spent=spent_gpu,
        gpu_time_limit=limit_gpu,
        cpu_time_spent=spent_cpu,
        cpu_time_limit=limit_cpu,
    )
