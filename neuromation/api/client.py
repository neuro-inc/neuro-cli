import ssl
from types import TracebackType
from typing import Optional, Type

import aiohttp
import certifi

from .config import _Config
from .core import DEFAULT_TIMEOUT, _Core
from .images import _Images
from .jobs import _Jobs
from .models import _Models
from .storage import _Storage
from .users import _Users


class Client:
    def __init__(
        self, config: _Config, *, timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT
    ) -> None:
        self._config = config
        self._ssl_context = ssl.SSLContext()
        self._ssl_context.load_verify_locations(capath=certifi.where())
        self._connector = aiohttp.TCPConnector(ssl=self._ssl_context)
        self._core = _Core(
            self._connector, self._config.url, self._config.auth_token.token, timeout
        )
        self._jobs = _Jobs(self._core, self._config)
        self._models = _Models(self._core)
        self._storage = _Storage(self._core, self._config)
        self._users = _Users(self._core)
        self._images: Optional[_Images] = None

    async def close(self) -> None:
        await self._core.close()
        if self._images is not None:
            await self._images.close()
        await self._connector.close()

    async def __aenter__(self) -> "Client":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional[TracebackType] = None,
    ) -> None:
        await self.close()

    @property
    def username(self) -> str:
        return self._config.auth_token.username

    @property
    def jobs(self) -> _Jobs:
        return self._jobs

    @property
    def models(self) -> _Models:
        return self._models

    @property
    def storage(self) -> _Storage:
        return self._storage

    @property
    def users(self) -> _Users:
        return self._users

    @property
    def images(self) -> _Images:
        if self._images is None:
            self._images = _Images(self._core, self._config)
        return self._images
