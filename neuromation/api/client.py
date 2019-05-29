from types import TracebackType
from typing import Optional, Type

import aiohttp

from .config import _Config
from .core import DEFAULT_TIMEOUT, _Core
from .images import Images
from .jobs import Jobs
from .storage import Storage
from .users import Users
from .utils import NoPublicConstructor


class Client(metaclass=NoPublicConstructor):
    def __init__(
        self,
        connector: aiohttp.BaseConnector,
        config: _Config,
        *,
        timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT
    ) -> None:
        config.check_initialized()
        self._config = config
        self._connector = connector
        self._core = _Core(
            connector, self._config.url, self._config.auth_token.token, timeout
        )
        self._jobs = Jobs._create(self._core, self._config)
        self._storage = Storage._create(self._core, self._config)
        self._users = Users._create(self._core)
        self._images: Optional[Images] = None

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
    def jobs(self) -> Jobs:
        return self._jobs

    @property
    def storage(self) -> Storage:
        return self._storage

    @property
    def users(self) -> Users:
        return self._users

    @property
    def images(self) -> Images:
        if self._images is None:
            self._images = Images._create(self._core, self._config)
        return self._images
