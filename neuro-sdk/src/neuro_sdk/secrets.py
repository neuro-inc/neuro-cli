import base64
from dataclasses import dataclass
from typing import AsyncIterator, Optional

from yarl import URL

from .config import Config
from .core import _Core
from .utils import NoPublicConstructor, asyncgeneratorcontextmanager


@dataclass(frozen=True)
class Secret:
    key: str
    owner: str
    cluster_name: str

    @property
    def uri(self) -> URL:
        return URL(f"secret://{self.cluster_name}/{self.owner}/{self.key}")


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
                    cluster_name=self._config.cluster_name,
                )

    async def add(
        self, key: str, value: bytes, cluster_name: Optional[str] = None
    ) -> None:
        url = self._get_secrets_url(cluster_name)
        auth = await self._config._api_auth()
        data = {
            "key": key,
            "value": base64.b64encode(value).decode("ascii"),
        }
        async with self._core.request("POST", url, auth=auth, json=data):
            pass

    async def rm(self, key: str, cluster_name: Optional[str] = None) -> None:
        url = self._get_secrets_url(cluster_name) / key
        auth = await self._config._api_auth()
        async with self._core.request("DELETE", url, auth=auth):
            pass
