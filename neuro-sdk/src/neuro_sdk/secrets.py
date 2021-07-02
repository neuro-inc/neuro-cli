import base64
from dataclasses import dataclass
from typing import AsyncIterator

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

    @asyncgeneratorcontextmanager
    async def list(self) -> AsyncIterator[Secret]:
        url = self._config.secrets_url
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            ret = await resp.json()
            for j in ret:
                yield Secret(
                    key=j["key"],
                    owner=j["owner"],
                    cluster_name=self._config.cluster_name,
                )

    async def add(self, key: str, value: bytes) -> None:
        url = self._config.secrets_url
        auth = await self._config._api_auth()
        data = {
            "key": key,
            "value": base64.b64encode(value).decode("ascii"),
        }
        async with self._core.request("POST", url, auth=auth, json=data):
            pass

    async def rm(self, key: str) -> None:
        url = self._config.secrets_url / key
        auth = await self._config._api_auth()
        async with self._core.request("DELETE", url, auth=auth):
            pass
