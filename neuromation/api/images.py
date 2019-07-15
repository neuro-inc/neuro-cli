import contextlib
import re
from dataclasses import replace
from typing import Dict, List, Optional

import aiodocker
import aiohttp
from aiodocker.exceptions import DockerError
from yarl import URL

from .abc import AbstractDockerImageProgress
from .config import _Config
from .core import AuthorizationError, _Core
from .parsing_utils import LocalImage, RemoteImage, _ImageNameParser
from .registry import _Registry
from .utils import NoPublicConstructor


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
                    900,
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

    async def _close(self) -> None:
        for image in self._temporary_images:
            with contextlib.suppress(DockerError, aiohttp.ClientError):
                await self._docker.images.delete(image)
        await self._docker.close()
        await self._registry.close()

    def _auth(self) -> Dict[str, str]:
        return {"username": "token", "password": self._config.auth_token.token}

    async def push(
        self,
        local_image: LocalImage,
        remote_image: Optional[RemoteImage] = None,
        *,
        progress: Optional[AbstractDockerImageProgress] = None,
    ) -> RemoteImage:
        if remote_image is None:
            parser = _ImageNameParser(
                self._config.auth_token.username,
                self._config.cluster_config.registry_url,
            )
            remote_image = parser.convert_to_neuro_image(local_image)

        local_str = str(local_image)
        remote_str = str(remote_image)

        if progress is None:
            progress = _DummyProgress()
        progress.start(local_str, remote_str)

        repo = remote_image.as_repo_str()
        try:
            await self._docker.images.tag(local_str, repo)
        except DockerError as error:
            if error.status == 404:
                raise ValueError(
                    f"Image {local_str} was not found " "in your local docker images"
                ) from error
        try:
            stream = await self._docker.images.push(
                repo, auth=self._auth(), stream=True
            )
        except DockerError as error:
            # TODO check this part when registry fixed
            if error.status == 403:
                raise AuthorizationError(f"Access denied {remote_str}") from error
            raise  # pragma: no cover
        async for obj in stream:
            if "error" in obj.keys():
                error_details = obj.get("errorDetail", {"message": "Unknown error"})
                raise DockerError(900, error_details)
            elif "id" in obj.keys() and obj["id"] != remote_image.tag:
                if "progress" in obj.keys():
                    message = f"{obj['id']}: {obj['status']} {obj['progress']}"
                else:
                    message = f"{obj['id']}: {obj['status']}"
                progress.progress(message, obj["id"])
        return remote_image

    async def pull(
        self,
        remote_image: RemoteImage,
        local_image: Optional[LocalImage] = None,
        *,
        progress: Optional[AbstractDockerImageProgress] = None,
    ) -> LocalImage:
        if local_image is None:
            parser = _ImageNameParser(
                self._config.auth_token.username,
                self._config.cluster_config.registry_url,
            )
            local_image = parser.convert_to_local_image(remote_image)

        local_str = str(local_image)
        remote_str = str(remote_image)

        if progress is None:
            progress = _DummyProgress()
        progress.start(remote_str, local_str)

        repo = remote_image.as_repo_str()
        try:
            stream = await self._docker.pull(
                repo, auth=self._auth(), repo=repo, stream=True
            )
            self._temporary_images.append(repo)
        except DockerError as error:
            if error.status == 404:
                raise ValueError(
                    f"Image {remote_str} was not found " "in registry"
                ) from error
            # TODO check this part when registry fixed
            elif error.status == 403:
                raise AuthorizationError(f"Access denied {remote_str}") from error
            raise  # pragma: no cover

        async for obj in stream:
            if "error" in obj.keys():
                error_details = obj.get("errorDetail", {"message": "Unknown error"})
                raise DockerError(900, error_details)
            elif "id" in obj.keys() and obj["id"] != remote_image.tag:
                if "progress" in obj.keys():
                    message = f"{obj['id']}: {obj['status']} {obj['progress']}"
                else:
                    message = f"{obj['id']}: {obj['status']}"
                progress.progress(message, obj["id"])

        await self._docker.images.tag(repo, local_str)

        return local_image

    async def ls(self) -> List[RemoteImage]:
        async with self._registry.request("GET", URL("_catalog")) as resp:
            parser = _ImageNameParser(
                self._config.auth_token.username,
                self._config.cluster_config.registry_url,
            )
            ret = await resp.json()
            prefix = "image://"
            result: List[RemoteImage] = []
            for repo in ret["repositories"]:
                if not repo.startswith(prefix):
                    repo = prefix + repo
                result.append(parser.parse_as_neuro_image(repo, allow_tag=False))
            return result

    async def tags(self, image: RemoteImage) -> List[RemoteImage]:
        if image.owner:
            name = f"{image.owner}/{image.name}"
        else:
            name = image.name
        async with self._registry.request("GET", URL(f"{name}/tags/list")) as resp:
            ret = await resp.json()
            return [replace(image, tag=tag) for tag in ret.get("tags", [])]


class _DummyProgress(AbstractDockerImageProgress):
    def start(self, src: str, dst: str) -> None:
        pass

    def progress(self, message: str, layer_id: str) -> None:
        pass

    def close(self) -> None:
        pass
