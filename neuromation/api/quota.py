from dataclasses import dataclass
from typing import Any, Dict, Optional

from yarl import URL

from neuromation.api.config import _Config
from neuromation.api.core import _Core
from neuromation.api.utils import NoPublicConstructor


@dataclass(frozen=True)
class QuotaInfo:
    name: str

    cpu_time_spent: float
    cpu_time_limit: float

    gpu_time_spent: float
    gpu_time_limit: float

    @property
    def cpu_time_remaining(self) -> float:
        return self._get_remaining_time(self.cpu_time_spent, self.cpu_time_limit)

    @property
    def gpu_time_remaining(self) -> float:
        return self._get_remaining_time(self.gpu_time_spent, self.gpu_time_limit)

    def _get_remaining_time(self, time_spent: float, time_limit: float) -> float:
        if time_limit > time_spent:
            return time_limit - time_spent
        return 0.0


class Quota(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: _Config) -> None:
        self._core = core
        self._config = config

    async def get(self, user: Optional[str] = None) -> QuotaInfo:
        user = user or self._config.auth_token.username
        url = URL(f"stats/users/{user}")
        async with self._core.request("GET", url) as resp:
            res = await resp.json()
            return _quota_info_from_api(res)


def _quota_info_from_api(payload: Dict[str, Any]) -> QuotaInfo:
    jobs = payload["jobs"]
    spent_gpu_minutes = int(jobs["total_gpu_run_time_minutes"])
    spent_cpu_minutes = int(jobs["total_non_gpu_run_time_minutes"])

    quota = payload["quota"]
    limit_gpu_minutes_str = quota.get("total_gpu_run_time_minutes")
    limit_gpu_seconds = (
        float(limit_gpu_minutes_str) * 60 if limit_gpu_minutes_str else float("inf")
    )
    limit_cpu_minutes_str = quota.get("total_non_gpu_run_time_minutes")
    limit_cpu_seconds = (
        float(limit_cpu_minutes_str) * 60 if limit_cpu_minutes_str else float("inf")
    )

    return QuotaInfo(
        name=payload["name"],
        cpu_time_spent=float(spent_cpu_minutes) * 60,
        gpu_time_spent=float(spent_gpu_minutes) * 60,
        cpu_time_limit=limit_cpu_seconds,
        gpu_time_limit=limit_gpu_seconds,
    )
