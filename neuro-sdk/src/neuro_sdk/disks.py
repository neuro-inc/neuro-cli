import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncIterator, Mapping, Optional

from dateutil.parser import isoparse
from yarl import URL

from .config import Config
from .core import _Core
from .utils import NoPublicConstructor

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Disk:
    id: str
    storage: int  # In bytes
    owner: str
    status: "Disk.Status"
    cluster_name: str
    created_at: datetime
    last_usage: Optional[datetime] = None
    name: Optional[str] = None
    timeout_unused: Optional[timedelta] = None
    used_bytes: Optional[int] = None

    @property
    def life_span(self) -> Optional[timedelta]:
        logger.warning(
            "Disk.life_span property is deprecated, "
            "please use Disk.timeout_unused instead"
        )
        return self.timeout_unused

    @property
    def uri(self) -> URL:
        return URL(f"disk://{self.cluster_name}/{self.owner}/{self.id}")

    class Status(Enum):
        PENDING = "Pending"
        READY = "Ready"
        BROKEN = "Broken"


class Disks(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: Config) -> None:
        self._core = core
        self._config = config

    def _parse_disk_payload(self, payload: Mapping[str, Any]) -> Disk:
        last_usage_raw = payload.get("last_usage")
        if last_usage_raw is not None:
            last_usage: Optional[datetime] = isoparse(last_usage_raw)
        else:
            last_usage = None
        life_span_raw = payload.get("life_span")
        if life_span_raw is not None:
            timeout_unused: Optional[timedelta] = timedelta(seconds=life_span_raw)
        else:
            timeout_unused = None
        return Disk(
            id=payload["id"],
            storage=payload["storage"],
            used_bytes=payload.get("used_bytes"),
            owner=payload["owner"],
            name=payload.get("name"),
            status=Disk.Status(payload["status"]),
            cluster_name=self._config.cluster_name,
            created_at=isoparse(payload["created_at"]),
            last_usage=last_usage,
            timeout_unused=timeout_unused,
        )

    async def list(self) -> AsyncIterator[Disk]:
        url = self._config.disk_api_url
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            ret = await resp.json()
            for disk_payload in ret:
                yield self._parse_disk_payload(disk_payload)

    async def create(
        self,
        storage: int,
        timeout_unused: Optional[timedelta] = None,
        name: Optional[str] = None,
    ) -> Disk:
        url = self._config.disk_api_url
        auth = await self._config._api_auth()
        data = {
            "storage": storage,
            "life_span": timeout_unused.total_seconds() if timeout_unused else None,
            "name": name,
        }
        async with self._core.request("POST", url, auth=auth, json=data) as resp:
            payload = await resp.json()
            return self._parse_disk_payload(payload)

    async def get(self, disk_id_or_name: str) -> Disk:
        url = self._config.disk_api_url / disk_id_or_name
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            payload = await resp.json()
            return self._parse_disk_payload(payload)

    async def rm(self, disk_id_or_name: str) -> None:
        url = self._config.disk_api_url / disk_id_or_name
        auth = await self._config._api_auth()
        async with self._core.request("DELETE", url, auth=auth):
            pass
