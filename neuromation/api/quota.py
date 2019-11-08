from dataclasses import dataclass
from typing import Any, Dict, Optional

from yarl import URL

from neuromation.api.config import _Config
from neuromation.api.core import _Core
from neuromation.api.utils import NoPublicConstructor


@dataclass(frozen=True)
class QuotaDetails:
    spent_minutes: int
    limit_minutes: Optional[int]

    @property
    def remain_minutes(self) -> Optional[int]:
        if self.limit_minutes is None:
            # remain: infinity
            return None
        if self.limit_minutes > self.spent_minutes:
            return self.limit_minutes - self.spent_minutes
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

    async def get(self) -> QuotaInfo:
        url = URL(f"stats/users/{self._config.auth_token.username}")
        async with self._core.request("GET", url) as resp:
            res = await resp.json()
            return _quota_info_from_api(res)


# TODO: test!
def _quota_info_from_api(payload: Dict[str, Any]) -> QuotaInfo:
    total_gpu_str = payload["quota"].get("total_gpu_run_time_minutes")
    total_cpu_str = payload["quota"].get("total_non_gpu_run_time_minutes")

    gpu_details = QuotaDetails(
        spent_minutes=int(payload["jobs"]["total_gpu_run_time_minutes"]),
        limit_minutes=int(total_gpu_str) if total_gpu_str else None,
    )
    cpu_details = QuotaDetails(
        spent_minutes=int(payload["jobs"]["total_non_gpu_run_time_minutes"]),
        limit_minutes=int(total_cpu_str) if total_gpu_str else None,
    )
    return QuotaInfo(
        name=payload["name"], gpu_details=gpu_details, cpu_details=cpu_details
    )
