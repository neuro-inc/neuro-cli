from types import TracebackType
from typing import Union, Type, Optional

import aiohttp
from yarl import URL

from .abc import AbstractProgress, AbstractSpinner
from .api import (
    API,
    ResourceNotFound,
    ClientError,
    IllegalArgumentError,
    AuthError,
    AuthenticationError,
    AuthorizationError,
    DEFAULT_TIMEOUT,
)
from .jobs import (
    Jobs,
    Image,
    JobDescription,
    JobStatus,
    JobStatusHistory,
    NetworkPortForwarding,
    Resources,
    Volume,
    Container,
    JobTelemetry,
)
from .models import Models, TrainResult
from .storage import Storage, FileStatusType, FileStatus
from .users import Action, Permission, Users
from .images import Images
from .config import Config

__all__ = (
    "Image",
    "JobDescription",
    "JobStatus",
    "JobStatusHistory",
    "JobTelemetry",
    "NetworkPortForwarding",
    "Resources",
    "Volume",
    "TrainResult",
    "Action",
    "Permission",
    "Client",
    "FileStatusType",
    "FileStatus",
    "Container",
    "ResourceNotFound",
    "ClientError",
    "IllegalArgumentError",
    "AuthError",
    "AuthenticationError",
    "AuthorizationError",
    "AbstractProgress",
    "AbstractSpinner",
)


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
        self._config = Config(url, self._registry_url, token)
        self._api = API(url, token, timeout)
        self._jobs = Jobs(self._api, token)
        self._models = Models(self._api)
        self._storage = Storage(self._api, self._config)
        self._users = Users(self._api)
        self._images: Optional[Images] = None

    async def close(self) -> None:
        await self._api.close()
        if self._images is not None:
            await self._images.close()

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
        return self._config.username

    @property
    def cfg(self) -> Config:
        return self._config

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
            self._images = Images(self._api, self._config)
        return self._images
