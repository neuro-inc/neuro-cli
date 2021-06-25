import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncIterator, Mapping, Optional, Tuple

from dateutil.parser import isoparse

from .config import Config
from .core import _Core
from .utils import NoPublicConstructor, asyncgeneratorcontextmanager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ServiceAccount:
    id: str
    name: Optional[str]
    owner: str
    default_cluster: str
    role: str
    created_at: datetime


class ServiceAccounts(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: Config) -> None:
        self._core = core
        self._config = config

    def _parse_account_payload(self, payload: Mapping[str, Any]) -> ServiceAccount:
        return ServiceAccount(
            id=payload["id"],
            owner=payload["owner"],
            name=payload["name"],
            default_cluster=payload["default_cluster"],
            role=payload["role"],
            created_at=isoparse(payload["created_at"]),
        )

    @asyncgeneratorcontextmanager
    async def list(self) -> AsyncIterator[ServiceAccount]:
        url = self._config.service_accounts_url
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            ret = await resp.json()
            for item in ret:
                yield self._parse_account_payload(item)

    async def create(
        self,
        name: Optional[str] = None,
        default_cluster: Optional[str] = None,
    ) -> Tuple[ServiceAccount, str]:
        url = self._config.service_accounts_url
        auth = await self._config._api_auth()
        data = {
            "name": name,
            "default_cluster": default_cluster or self._config.cluster_name,
        }
        async with self._core.request("POST", url, auth=auth, json=data) as resp:
            payload = await resp.json()
            return self._parse_account_payload(payload), payload["token"]

    async def get(self, id_or_name: str) -> ServiceAccount:
        url = self._config.service_accounts_url / id_or_name
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            payload = await resp.json()
            return self._parse_account_payload(payload)

    async def rm(self, id_or_name: str) -> None:
        url = self._config.service_accounts_url / id_or_name
        auth = await self._config._api_auth()
        async with self._core.request("DELETE", url, auth=auth):
            pass
