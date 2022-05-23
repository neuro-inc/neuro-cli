import base64
from dataclasses import dataclass
from typing import AsyncIterator, Optional, Union

from yarl import URL

from ._config import Config
from ._core import _Core
from ._rewrite import rewrite_module
from ._utils import (
    NoPublicConstructor,
    OrgNameSentinel,
    asyncgeneratorcontextmanager,
    org_name_sentinel,
)


@rewrite_module
@dataclass(frozen=True)
class Secret:
    key: str
    owner: str
    cluster_name: str
    org_name: Optional[str]

    @property
    def uri(self) -> URL:
        base = f"secret://{self.cluster_name}"
        if self.org_name:
            base += f"/{self.org_name}"
        return URL(f"{base}/{self.owner}/{self.key}")


@rewrite_module
class Secrets(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: Config) -> None:
        self._core = core
        self._config = config

    def _get_secrets_url(self, cluster_name: Optional[str]) -> URL:
        if cluster_name is None:
            cluster_name = self._config.cluster_name
        return self._config.get_cluster(cluster_name).secrets_url

    @asyncgeneratorcontextmanager
    async def list(self, cluster_name: Optional[str] = None) -> AsyncIterator[Secret]:
        url = self._get_secrets_url(cluster_name)
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            ret = await resp.json()
            for j in ret:
                yield Secret(
                    key=j["key"],
                    owner=j["owner"],
                    cluster_name=cluster_name or self._config.cluster_name,
                    org_name=j.get("org_name"),
                )

    async def add(
        self,
        key: str,
        value: bytes,
        cluster_name: Optional[str] = None,
        org_name: Union[Optional[str], OrgNameSentinel] = org_name_sentinel,
    ) -> None:
        url = self._get_secrets_url(cluster_name)
        auth = await self._config._api_auth()
        data = {
            "key": key,
            "value": base64.b64encode(value).decode("ascii"),
            "org_name": org_name
            if not isinstance(org_name, OrgNameSentinel)
            else self._config.org_name,
        }
        async with self._core.request("POST", url, auth=auth, json=data):
            pass

    async def rm(
        self,
        key: str,
        cluster_name: Optional[str] = None,
        org_name: Union[Optional[str], OrgNameSentinel] = org_name_sentinel,
    ) -> None:
        url = self._get_secrets_url(cluster_name) / key
        auth = await self._config._api_auth()
        params = {}
        org_name_val = (
            org_name
            if not isinstance(org_name, OrgNameSentinel)
            else self._config.org_name
        )
        if org_name_val:
            params["org_name"] = org_name_val
        async with self._core.request("DELETE", url, auth=auth, params=params):
            pass
