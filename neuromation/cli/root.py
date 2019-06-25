import logging
from dataclasses import dataclass
from http.cookies import Morsel  # noqa
from pathlib import Path
from typing import Dict, Optional, Tuple

import aiohttp
from yarl import URL

from neuromation.api import Client, Factory
from neuromation.api.config import _Config
from neuromation.api.config_factory import ConfigError
from neuromation.api.login import RunPreset


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
    _factory: Optional[Factory] = None
    verbosity: int = 0

    @property
    def _config(self) -> _Config:
        assert self._client is not None
        return self._client._config

    @property
    def quiet(self) -> bool:
        return self.verbosity < 0

    @property
    def auth(self) -> Optional[str]:
        if self._client is not None:
            return self._config.auth_token.token
        return None

    @property
    def timeout(self) -> aiohttp.ClientTimeout:
        return aiohttp.ClientTimeout(
            None, None, self.network_timeout, self.network_timeout
        )

    @property
    def username(self) -> str:
        if self._client is None:
            raise ConfigError("User is not registered, run 'neuro login'.")
        return self._config.auth_token.username

    @property
    def url(self) -> URL:
        if self._client is None:
            raise ConfigError("User is not registered, run 'neuro login'.")
        return self._config.url

    @property
    def registry_url(self) -> URL:
        if self._client is None or not self._config.cluster_config.is_initialized():
            raise ConfigError("User is not registered, run 'neuro login'.")
        return self._config.cluster_config.registry_url

    @property
    def resource_presets(self) -> Dict[str, RunPreset]:
        if self._client is None or not self._config.cluster_config.is_initialized():
            raise ConfigError("User is not registered, run 'neuro login'.")
        return self._config.cluster_config.resource_presets

    @property
    def client(self) -> Client:
        assert self._client is not None
        return self._client

    async def init_client(self) -> None:
        self._factory = Factory(path=self.config_path)
        client = await self._factory.get(timeout=self.timeout)

        self._client = client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()

    def get_session_cookie(self) -> Optional["Morsel[str]"]:
        if self._client is None:
            return None
        return self._client._get_session_cookie()
