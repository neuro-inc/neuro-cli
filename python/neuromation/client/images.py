import re
from contextlib import suppress
from dataclasses import dataclass
from typing import Dict, List

import aiodocker
import aiohttp
from aiodocker.exceptions import DockerError
from yarl import URL

from .abc import AbstractSpinner
from .api import API, AuthorizationError
from .config import Config
from .registry import Registry


STATUS_FORBIDDEN = 403
STATUS_NOT_FOUND = 404
STATUS_CUSTOM_ERROR = 900
DEFAULT_TAG = "latest"


@dataclass(frozen=True)
class Image:
    url: URL
    local: str

    @classmethod
    def from_url(cls, url: URL, username: str) -> "Image":
        if not url:
            raise ValueError(f"Image URL cannot be empty")
        if url.scheme != "image":
            raise ValueError(f"Invalid scheme, for image URL: {url}")
        if url.path == "/" or url.query or url.fragment or url.user or url.port:
            raise ValueError(f"Invalid image URL: {url}")
        colon_count = url.path.count(":")
        if colon_count > 1:
            raise ValueError(f"Invalid image URL, only one colon allowed: {url}")

        if not colon_count:
            url = url.with_path(f"{url.path}:{DEFAULT_TAG}")

        if not url.host:
            url = URL(f"image://{username}/{url.path.lstrip('/')}")

        return cls(url=url, local=url.path.lstrip("/"))

    @classmethod
    def from_local(cls, name: str, username: str) -> "Image":
        colon_count = name.count(":")
        if colon_count > 1:
            raise ValueError(f"Invalid image name, only one colon allowed: {name}")

        if not colon_count:
            name = f"{name}:{DEFAULT_TAG}"

        return cls(url=URL(f"image://{username}/{name}"), local=name)


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

    def _repo(self, image: Image) -> str:
        # TODO (ajuszkowski, 11-Feb-2019) here we use only registry host, not host:port
        return f"{self._config.registry_url.host}/{image.url.host}{image.url.path}"

    async def push(
        self, local_image: Image, remote_image: Image, spinner: AbstractSpinner
    ) -> Image:
        repo = self._repo(local_image)
        spinner.start("Pushing image ...")
        try:
            await self._docker.images.tag(local_image.local, repo)
        except DockerError as error:
            spinner.complete()
            if error.status == STATUS_NOT_FOUND:
                raise ValueError(
                    f"Image {local_image.local} was not found "
                    "in your local docker images"
                ) from error
        spinner.tick()
        try:
            stream = await self._docker.images.push(
                repo, auth=self._auth(), stream=True
            )
            spinner.tick()
        except DockerError as error:
            spinner.complete()
            # TODO check this part when registry fixed
            if error.status == STATUS_FORBIDDEN:
                raise AuthorizationError(f"Access denied {remote_image.url}") from error
            raise  # pragma: no cover
        async for obj in stream:
            spinner.tick()
            if "error" in obj.keys():
                spinner.complete()
                error_details = obj.get("errorDetail", {"message": "Unknown error"})
                raise DockerError(STATUS_CUSTOM_ERROR, error_details)
        spinner.complete()
        return remote_image

    async def pull(
        self, remote_image: Image, local_image: Image, spinner: AbstractSpinner
    ) -> Image:
        repo = self._repo(remote_image)
        spinner.start("Pulling image ...")
        try:
            stream = await self._docker.pull(
                repo, auth=self._auth(), repo=repo, stream=True
            )
            self._temporary_images.append(repo)
        except DockerError as error:
            spinner.complete()
            if error.status == STATUS_NOT_FOUND:
                raise ValueError(
                    f"Image {remote_image.url} was not found " "in registry"
                ) from error
            # TODO check this part when registry fixed
            elif error.status == STATUS_FORBIDDEN:
                raise AuthorizationError(f"Access denied {remote_image.url}") from error
            raise  # pragma: no cover
        spinner.tick()

        async for obj in stream:
            spinner.tick()
            if "error" in obj.keys():
                spinner.complete()
                error_details = obj.get("errorDetail", {"message": "Unknown error"})
                raise DockerError(STATUS_CUSTOM_ERROR, error_details)
        spinner.tick()

        await self._docker.images.tag(repo, local_image.local)
        spinner.complete()

        return local_image

    async def ls(self) -> List[URL]:
        async with self._registry.request("GET", URL("_catalog")) as resp:
            ret = await resp.json()
            return [URL(name) for name in ret["repositories"]]
