import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import aiohttp
from yarl import URL

from neuromation.api import Client, get as api_get
from neuromation.api.config import _Config
from neuromation.api.config_factory import RCException


log = logging.getLogger(__name__)


@dataclass
class Root:
    color: bool
    tty: bool
    terminal_size: Tuple[int, int]
    disable_pypi_version_check: bool
    network_timeout: float
    config_path: Path

    _config: Optional[_Config] = None
    _client: Optional[Client] = None

    @property
    def auth(self) -> Optional[str]:
        if self._config is not None:
            return self._config.auth_token.token
        return None

    def get_platform_user_name(self) -> Optional[str]:
        # TODO: drop the method, use self.username
        if self._config is not None:
            return self._config.auth_token.username
        return None

    @property
    def timeout(self) -> aiohttp.ClientTimeout:
        return aiohttp.ClientTimeout(
            None, None, self.network_timeout, self.network_timeout
        )

    @property
    def username(self) -> str:
        if self._config is None:
            raise RCException("User is not registered, run 'neuro login'.")
        return self._config.auth_token.username

    @property
    def url(self) -> URL:
        if self._config is None:
            raise RCException("User is not registered, run 'neuro login'.")
        return self._config.url

    @property
    def registry_url(self) -> URL:
        if self._config is None:
            raise RCException("User is not registered, run 'neuro login'.")
        return self._config.registry_url

    @property
    def client(self) -> Client:
        assert self._client is not None
        return self._client

    async def post_init(self) -> None:
        client = await api_get(path=self.config_path, timeout=self.timeout)

        self._client = client
        self._config = client._config

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()

    def make_client(self) -> Client:
        # TODO: drop the method, use self.client
        return self.client
