from dataclasses import dataclass
from typing import Any, Dict, Optional

from yarl import URL

from neuromation.api.config import _Config
from neuromation.api.core import _Core
from neuromation.api.utils import NoPublicConstructor


@dataclass(frozen=True)
class QuotaInfo:
    name: str
    spent_gpu_minutes: int
    spent_non_gpu_minutes: int
    quota_gpu_minutes: Optional[int]
    quota_non_gpu_minutes: Optional[int]


class Quota(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: _Config) -> None:
        self._core = core
        self._config = config

    async def get(self) -> QuotaInfo:
        url = URL(f"stats/users/{self._config.auth_token.username}")
        async with self._core.request("GET", url) as resp:
            res = await resp.json()
            return _quota_info_from_api(res)


def _quota_info_from_api(payload: Dict[str, Any]) -> QuotaInfo:
    total_gpu_str = payload["quota"].get("total_gpu_run_time_minutes")
    total_non_gpu_str = payload["quota"].get("total_non_gpu_run_time_minutes")
    return QuotaInfo(
        name=payload["name"],
        spent_gpu_minutes=int(payload["jobs"]["total_gpu_run_time_minutes"]),
        spent_non_gpu_minutes=int(payload["jobs"]["total_non_gpu_run_time_minutes"]),
        quota_gpu_minutes=int(total_gpu_str) if total_gpu_str else None,
        quota_non_gpu_minutes=int(total_non_gpu_str) if total_non_gpu_str else None,
    )
