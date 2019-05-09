import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import aiohttp
from yarl import URL

from neuromation.api import Client, get as api_get
from neuromation.api.config import _Config
from neuromation.api.config_factory import ConfigError


log = logging.getLogger(__name__)


@dataclass
class Root:
    color: bool
    tty: bool
    terminal_size: Tuple[int, int]
    disable_pypi_version_check: bool
    network_timeout: float
    config_path: Path

    _client: Optional[Client] = None

    @property
    def _config(self) -> Optional[_Config]:
        if self._client is None:
            return None
        return self._client._config

    @property
    def auth(self) -> Optional[str]:
        if self._config is not None:
            return self._config.auth_token.token
        return None

    @property
    def timeout(self) -> aiohttp.ClientTimeout:
        return aiohttp.ClientTimeout(
            None, None, self.network_timeout, self.network_timeout
        )

    @property
    def username(self) -> str:
        if self._config is None:
            raise ConfigError("User is not registered, run 'neuro login'.")
        return self._config.auth_token.username

    @property
    def url(self) -> URL:
        if self._config is None:
            raise ConfigError("User is not registered, run 'neuro login'.")
        return self._config.url

    @property
    def registry_url(self) -> URL:
        if self._config is None or not self._config.cluster_config.is_initialized():
            raise ConfigError("User is not registered, run 'neuro login'.")
        return self._config.cluster_config.registry_url

    @property
    def client(self) -> Client:
        assert self._client is not None
        return self._client

    async def init_client(self) -> None:
        client = await api_get(path=self.config_path, timeout=self.timeout)

        self._client = client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
