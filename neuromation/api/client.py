import ssl
from types import TracebackType
from typing import Optional, Type, Union

import aiohttp
import certifi
from yarl import URL

from .config import _Config
from .core import DEFAULT_TIMEOUT, Core
from .images import Images
from .jobs import Jobs
from .models import Models
from .storage import Storage
from .users import Users


class Client:
    def __init__(
        self,
        url: Union[URL, str],
        token: str,
        *,
        registry_url: str = "",
        timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT,
    ) -> None:
        if isinstance(url, str):
            url = URL(url)
        self._url = url
        self._registry_url = URL(registry_url)
        assert token
        self._config = _Config(url, self._registry_url, token)
        self._ssl_context = ssl.SSLContext()
        self._ssl_context.load_verify_locations(capath=certifi.where())
        self._connector = aiohttp.TCPConnector(ssl=self._ssl_context)
        self._core = Core(self._connector, url, token, timeout)
        self._jobs = Jobs(self._core, token)
        self._models = Models(self._core)
        self._storage = Storage(self._core, self._config)
        self._users = Users(self._core)
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
    def jobs(self) -> Jobs:
        return self._jobs

    @property
    def models(self) -> Models:
        return self._models

    @property
    def storage(self) -> Storage:
        return self._storage

    @property
    def users(self) -> Users:
        return self._users

    @property
    def images(self) -> Images:
        if self._images is None:
            self._images = Images(self._core, self._config)
        return self._images
