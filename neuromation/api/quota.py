from dataclasses import dataclass
from typing import Any, Dict, Optional

from yarl import URL

from neuromation.api.config import _Config
from neuromation.api.core import _Core
from neuromation.api.utils import NoPublicConstructor


@dataclass(frozen=True)
class QuotaDetails:
    # all fields: in seconds
    time_spent: float
    time_limit: Optional[float]

    @property
    def time_remain(self) -> Optional[float]:
        if self.time_limit is None:
            # remain: infinity
            return None
        if self.time_limit > self.time_spent:
            return self.time_limit - self.time_spent
        return 0


@dataclass(frozen=True)
class QuotaInfo:
    name: str
    gpu_details: QuotaDetails
    cpu_details: QuotaDetails


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
    jobs_gpu_minutes = int(jobs["total_gpu_run_time_minutes"])
    jobs_cpu_minutes = int(jobs["total_non_gpu_run_time_minutes"])
    quota = payload["quota"]
    quota_gpu_minutes_str = quota.get("total_gpu_run_time_minutes")
    quota_cpu_minutes_str = quota.get("total_non_gpu_run_time_minutes")

    gpu_details = QuotaDetails(
        time_spent=float(jobs_gpu_minutes) * 60,
        time_limit=float(quota_gpu_minutes_str) * 60 if quota_gpu_minutes_str else None,
    )
    cpu_details = QuotaDetails(
        time_spent=float(jobs_cpu_minutes) * 60,
        time_limit=float(quota_cpu_minutes_str) * 60 if quota_gpu_minutes_str else None,
    )
    return QuotaInfo(
        name=payload["name"], gpu_details=gpu_details, cpu_details=cpu_details
    )
