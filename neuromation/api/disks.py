from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncIterator, Mapping

from yarl import URL

from .config import Config
from .core import _Core
from .utils import NoPublicConstructor


@dataclass(frozen=True)
class Disk:
    id: str
    storage: int  # In bytes
    owner: str
    status: "Disk.Status"
    cluster_name: str

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
        return Disk(
            id=payload["id"],
            storage=payload["storage"],
            owner=payload["owner"],
            status=Disk.Status(payload["status"]),
            cluster_name=self._config.cluster_name,
        )

    async def list(self) -> AsyncIterator[Disk]:
        url = self._config.disk_api_url
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            ret = await resp.json()
            for disk_payload in ret:
                yield self._parse_disk_payload(disk_payload)

    async def create(self, storage: int) -> Disk:
        url = self._config.disk_api_url
        auth = await self._config._api_auth()
        data = {
            "storage": storage,
        }
        async with self._core.request("POST", url, auth=auth, json=data) as resp:
            payload = await resp.json()
            return self._parse_disk_payload(payload)

    async def get(self, disk_id: str) -> Disk:
        url = self._config.disk_api_url / disk_id
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            payload = await resp.json()
            return self._parse_disk_payload(payload)

    async def rm(self, disk_id: str) -> None:
        url = self._config.disk_api_url / disk_id
        auth = await self._config._api_auth()
        async with self._core.request("DELETE", url, auth=auth):
            pass
