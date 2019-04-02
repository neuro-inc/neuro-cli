import logging
import re
from contextlib import suppress
from dataclasses import dataclass
from typing import Dict, List, Optional

import aiodocker
import aiohttp
from aiodocker.exceptions import DockerError
from yarl import URL

from .abc import AbstractTreeProgress
from .api import API, AuthorizationError
from .config import Config
from .registry import Registry


STATUS_FORBIDDEN = 403
STATUS_NOT_FOUND = 404
STATUS_CUSTOM_ERROR = 900

log = logging.getLogger(__name__)

IMAGE_SCHEME = "image"


@dataclass(frozen=True)
# TODO (ajuszkowski, 20-feb-2019): rename this class: docker-images refer to both local
# images and images in docker hub, and neuro-images refer to an image in neuro registry
class DockerImage:
    name: str
    tag: str = "latest"
    owner: Optional[str] = None
    registry: Optional[str] = None

    def is_in_neuro_registry(self) -> bool:
        return bool(self.registry and self.owner)

    def as_url_str(self) -> str:
        pre = f"{IMAGE_SCHEME}://{self.owner}/" if self.is_in_neuro_registry() else ""
        return f"{pre}{self.name}:{self.tag}"

    def as_repo_str(self) -> str:
        # TODO (ajuszkowski, 11-Feb-2019) should be host:port (see URL.explicit_port)
        pre = f"{self.registry}/{self.owner}/" if self.is_in_neuro_registry() else ""
        return pre + self.as_local_str()

    def as_local_str(self) -> str:
        return f"{self.name}:{self.tag}"


class Images:
    def __init__(self, api: API, config: Config) -> None:
        self._api = api
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
        self._registry = Registry(
            self._api.connector,
            self._config.registry_url.with_path("/v2/"),
            self._config.token,
            self._config.username,
        )

    async def close(self) -> None:
        for image in self._temporary_images:
            with suppress(DockerError, aiohttp.ClientError):
                await self._docker.images.delete(image)
        await self._docker.close()
        await self._registry.close()

    def _auth(self) -> Dict[str, str]:
        return {"username": "token", "password": self._config.token}

    async def push(
        self,
        local_image: DockerImage,
        remote_image: DockerImage,
        progress: AbstractTreeProgress,
    ) -> DockerImage:
        repo = remote_image.as_repo_str()
        progress.message("Pushing image ...")
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
                progress.message(message, obj["id"])
        progress.message("Done")
        return remote_image

    async def pull(
        self,
        remote_image: DockerImage,
        local_image: DockerImage,
        progress: AbstractTreeProgress,
    ) -> DockerImage:
        repo = remote_image.as_repo_str()
        progress.message("Pulling image...")
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
                progress.message(message, obj["id"])

        await self._docker.images.tag(repo, local_image.as_local_str())

        return local_image

    async def ls(self) -> List[URL]:
        async with self._registry.request("GET", URL("_catalog")) as resp:
            ret = await resp.json()
            return [URL(name) for name in ret["repositories"]]
