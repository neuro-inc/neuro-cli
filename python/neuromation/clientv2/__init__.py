from types import TracebackType
from typing import Union, Type, Optional

import aiohttp
from jose import jwt
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
)
from .models import Models, TrainResult
from .storage import Storage, FileStatusType, FileStatus
from .users import Action, Permission, Users
from .images import Images

__all__ = (
    "Image",
    "JobDescription",
    "JobStatus",
    "JobStatusHistory",
    "NetworkPortForwarding",
    "Resources",
    "Volume",
    "TrainResult",
    "Action",
    "Permission",
    "ClientV2",
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

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(None, None, 30, 30)


class ClientV2:
    def __init__(
        self,
        url: Union[URL, str],
        token: str,
        *,
        timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT,
    ) -> None:
        if isinstance(url, str):
            url = URL(url)
        self._url = url
        assert token
        jwt_data = jwt.get_unverified_claims(token)
        self._token = token
        self._username = jwt_data.get("identity", None)
        self._api = API(url, token, timeout)
        self._jobs = Jobs(self._api)
        self._models = Models(self._api)
        self._storage = Storage(self._api, self._username)
        self._users = Users(self._api)
        self._images: Optional[Image] = None

    async def close(self) -> None:
        await self._api.close()
        if self._images is not None:
            await self._images.close()

    async def __aenter__(self) -> "ClientV2":
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
        return self._username

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
            self._images = Images(self._api, self._url, self._token, self._username)
        return self._images
