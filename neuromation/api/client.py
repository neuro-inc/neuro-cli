import time
from http.cookies import Morsel  # noqa
from http.cookies import SimpleCookie
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


SESSION_COOKIE_MAXAGE = 5 * 60  # 5 min


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
        if time.time() - config.cookie_session.timestamp > SESSION_COOKIE_MAXAGE:
            # expired
            cookie: Optional["Morsel[str]"] = None
        else:
            tmp = SimpleCookie()
            tmp["NEURO_SESSION"] = config.cookie_session.cookie
            cookie = tmp["NEURO_SESSION"]
            assert config.url.raw_host is not None
            cookie["domain"] = config.url.raw_host
            cookie["path"] = "/"
        self._core = _Core(
            connector, self._config.url, self._config.auth_token.token, cookie, timeout
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

    def _get_session_cookie(self) -> Optional["Morsel[str]"]:
        for cookie in self._core._session.cookie_jar:
            if cookie.key == "NEURO_SESSION":
                return cookie
        return None
