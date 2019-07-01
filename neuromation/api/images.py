import logging
import re
from contextlib import suppress
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import aiodocker
import aiohttp
from aiodocker.exceptions import DockerError
from yarl import URL

from .abc import AbstractDockerImageProgress
from .config import _Config
from .core import AuthorizationError, _Core
from .registry import _Registry
from .utils import NoPublicConstructor


STATUS_FORBIDDEN = 403
STATUS_NOT_FOUND = 404
STATUS_CUSTOM_ERROR = 900

log = logging.getLogger(__name__)

IMAGE_SCHEME = "image"


class DockerImageOperation(str, Enum):
    PUSH = "push"
    PULL = "pull"


@dataclass(frozen=True)
# TODO (ajuszkowski, 20-feb-2019): rename this class: docker-images refer to both local
# images and images in docker hub, and neuro-images refer to an image in neuro registry
class DockerImage:
    name: str
    tag: Optional[str] = None
    owner: Optional[str] = None
    registry: Optional[str] = None

    def is_in_neuro_registry(self) -> bool:
        return bool(self.registry and self.owner)

    def as_url_str(self) -> str:
        pre = f"{IMAGE_SCHEME}://{self.owner}/" if self.is_in_neuro_registry() else ""
        post = f":{self.tag}" if self.tag else ""
        return pre + self.name + post

    def as_repo_str(self) -> str:
        # TODO (ajuszkowski, 11-Feb-2019) should be host:port (see URL.explicit_port)
        pre = f"{self.registry}/{self.owner}/" if self.is_in_neuro_registry() else ""
        return pre + self.as_local_str()

    def as_local_str(self) -> str:
        post = f":{self.tag}" if self.tag else ""
        return self.name + post


class Images(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: _Config) -> None:
        self._core = core
        self._config = config
        self._temporary_images: List[str] = list()
        try:
            self._docker = aiodocker.Docker()
        except ValueError as error:
            if re.match(
                r".*Either DOCKER_HOST or local sockets are not available.*", f"{error}"
            ):
                raise DockerError(
                    STATUS_CUSTOM_ERROR,
                    {
                        "message": "Docker engine is not available. "
                        "Please specify DOCKER_HOST variable "
                        "if you are using remote docker engine"
                    },
                )
            raise
        self._registry = _Registry(
            self._core.connector,
            self._config.cluster_config.registry_url.with_path("/v2/"),
            self._config.auth_token.token,
            self._config.auth_token.username,
        )

    async def close(self) -> None:
        for image in self._temporary_images:
            with suppress(DockerError, aiohttp.ClientError):
                await self._docker.images.delete(image)
        await self._docker.close()
        await self._registry.close()

    def _auth(self) -> Dict[str, str]:
        return {"username": "token", "password": self._config.auth_token.token}

    async def push(
        self,
        local_image: DockerImage,
        remote_image: DockerImage,
        progress: AbstractDockerImageProgress,
    ) -> DockerImage:
        repo = remote_image.as_repo_str()
        try:
            await self._docker.images.tag(local_image.as_local_str(), repo)
        except DockerError as error:
            if error.status == STATUS_NOT_FOUND:
                raise ValueError(
                    f"Image {local_image.as_local_str()} was not found "
                    "in your local docker images"
                ) from error
        try:
            stream = await self._docker.images.push(
                repo, auth=self._auth(), stream=True
            )
        except DockerError as error:
            # TODO check this part when registry fixed
            if error.status == STATUS_FORBIDDEN:
                raise AuthorizationError(
                    f"Access denied {remote_image.as_url_str()}"
                ) from error
            raise  # pragma: no cover
        async for obj in stream:
            if "error" in obj.keys():
                error_details = obj.get("errorDetail", {"message": "Unknown error"})
                raise DockerError(STATUS_CUSTOM_ERROR, error_details)
            elif "id" in obj.keys() and obj["id"] != remote_image.tag:
                if "progress" in obj.keys():
                    message = f"{obj['id']}: {obj['status']} {obj['progress']}"
                else:
                    message = f"{obj['id']}: {obj['status']}"
                progress(message, obj["id"])
        return remote_image

    async def pull(
        self,
        remote_image: DockerImage,
        local_image: DockerImage,
        progress: AbstractDockerImageProgress,
    ) -> DockerImage:
        repo = remote_image.as_repo_str()
        try:
            stream = await self._docker.pull(
                repo, auth=self._auth(), repo=repo, stream=True
            )
            self._temporary_images.append(repo)
        except DockerError as error:
            if error.status == STATUS_NOT_FOUND:
                raise ValueError(
                    f"Image {remote_image.as_url_str()} was not found " "in registry"
                ) from error
            # TODO check this part when registry fixed
            elif error.status == STATUS_FORBIDDEN:
                raise AuthorizationError(
                    f"Access denied {remote_image.as_url_str()}"
                ) from error
            raise  # pragma: no cover

        async for obj in stream:
            if "error" in obj.keys():
                error_details = obj.get("errorDetail", {"message": "Unknown error"})
                raise DockerError(STATUS_CUSTOM_ERROR, error_details)
            elif "id" in obj.keys() and obj["id"] != remote_image.tag:
                if "progress" in obj.keys():
                    message = f"{obj['id']}: {obj['status']} {obj['progress']}"
                else:
                    message = f"{obj['id']}: {obj['status']}"
                progress(message, obj["id"])

        await self._docker.images.tag(repo, local_image.as_local_str())

        return local_image

    async def ls(self) -> List[URL]:
        async with self._registry.request("GET", URL("_catalog")) as resp:
            ret = await resp.json()
            result = []
            for name in ret["repositories"]:
                if name.startswith("image://"):
                    url = URL(name)
                else:
                    url = URL(f"image://{name}")
                result.append(url)
            return result
