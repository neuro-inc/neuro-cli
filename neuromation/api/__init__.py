from pathlib import Path

from yarl import URL

from .abc import AbstractProgress, AbstractSpinner
from .client import Client
from .config_factory import Factory
from .core import (
    AuthenticationError,
    AuthError,
    AuthorizationError,
    ClientError,
    IllegalArgumentError,
    ResourceNotFound,
)
from .images import DockerImage
from .jobs import (
    Container,
    HTTPPort,
    Image,
    JobDescription,
    JobStatus,
    JobStatusHistory,
    JobTelemetry,
    NetworkPortForwarding,
    Resources,
    Volume,
)
from .models import TrainResult
from .parsing_utils import ImageNameParser
from .storage import FileStatus, FileStatusType
from .users import Action, Permission


__all__ = (
    "Image",
    "ImageNameParser",
    "JobDescription",
    "JobStatus",
    "JobStatusHistory",
    "JobTelemetry",
    "NetworkPortForwarding",
    "Resources",
    "Volume",
    "HTTPPort",
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
    "ImageNameParser",
    "DockerImage",
    "Factory",
    "get",
    "login",
    "login_with_token",
    "logout",
)


_DEFAULT_NMRC_PATH = "~/.nmrc"


async def get(*, path: Path = _DEFAULT_NMRC_PATH) -> Client:
    return await Factory(path).get()


async def login(url: URL, *, path: Path = _DEFAULT_NMRC_PATH) -> Client:
    return await Factory(path).login(url)


async def login_with_token(
    url: URL, token: str, *, path: Path = _DEFAULT_NMRC_PATH
) -> Client:
    return await Factory(path).login_with_token(url, token)


async def logout(*, path: Path = _DEFAULT_NMRC_PATH) -> None:
    return await Factory(path).logout()
