import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List

import aiodocker
from aiodocker.exceptions import DockerError
from yarl import URL

from neuromation.clientv2 import AuthorizationError


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

    def to_repo(self, registry: str) -> str:
        return f"{registry}/{self.url.host}{self.url.path}"


class DockerHandler:
    """
    Docker-related manipulation handler
    At this moment image/registry  manipulations available
    """

    _PROGRESS = "|\\-/"
    _progress_tick = 0

    def _start_progress(self) -> None:
        self._progress_tick = 0
        self._tick_progress()

    def _tick_progress(self) -> None:
        self._progress_tick = (self._progress_tick + 1) % len(self._PROGRESS)
        if sys.stdout.isatty():  # pragma: no cover
            print(f"\r{self._PROGRESS[self._progress_tick]}", end="")

    def _end_progress(self) -> None:
        if sys.stdout.isatty():  # pragma: no cover
            print(f"\r", end="")

    def __init__(self, username: str, token: str, registry: URL) -> None:
        self._username = username
        self._token = token
        self._registry = registry
        try:
            self._client = aiodocker.Docker()
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
        self._temporary_images: List[str] = list()

    async def __aenter__(self) -> "DockerHandler":  # pragma: no cover
        return self

    async def __aexit__(
        self, exc_type: Any, exc_val: Any, exc_tb: Any
    ) -> None:  # pragma: no cover
        try:
            for image in self._temporary_images:
                await self._client.images.delete(image)
            await self._client.close()
        except BaseException:
            # Just ignore any error
            pass

    def _auth(self) -> Dict[str, str]:
        return {"username": "token", "password": self._token}

    async def push(self, image_name: str, remote_image_name: str) -> URL:
        local_image = remote_image = Image.from_local(image_name, self._username)
        if remote_image_name:
            remote_image = Image.from_url(URL(remote_image_name), self._username)

        repo = remote_image.to_repo(f"{self._registry.host}")
        self._start_progress()
        try:
            await self._client.images.tag(local_image.local, repo)
        except DockerError as error:
            self._end_progress()
            if error.status == STATUS_NOT_FOUND:
                raise ValueError(
                    f"Image {local_image.local} was not found "
                    "in your local docker images"
                ) from error
            raise  # pragma: no cover
        self._tick_progress()
        try:
            stream = await self._client.images.push(
                repo, auth=self._auth(), stream=True
            )
        except DockerError as error:
            self._end_progress()
            # TODO check this part when registry fixed
            if error.status == STATUS_FORBIDDEN:
                raise AuthorizationError(f"Access denied {remote_image.url}") from error
            raise  # pragma: no cover
        async for obj in stream:
            self._tick_progress()
            if "error" in obj.keys():
                self._end_progress()
                error_details = obj.get("errorDetail", {"message": "Unknown error"})
                raise DockerError(STATUS_CUSTOM_ERROR, error_details)
        self._end_progress()

        print(f"Image {local_image.local} pushed to registry as {remote_image.url}")
        return remote_image.url

    async def pull(self, image_name: str, local_image_name: str) -> str:
        remote_image = local_image = Image.from_url(URL(image_name), self._username)
        if local_image_name:
            local_image = Image.from_local(local_image_name, self._username)

        repo = remote_image.to_repo(f"{self._registry.host}")
        self._start_progress()
        try:
            stream = await self._client.pull(
                repo, auth=self._auth(), repo=repo, stream=True
            )
            self._temporary_images.append(repo)
        except DockerError as error:
            self._end_progress()
            if error.status == STATUS_NOT_FOUND:
                raise ValueError(
                    f"Image {remote_image.url} was not found " "in registry"
                ) from error
            # TODO check this part when registry fixed
            elif error.status == STATUS_FORBIDDEN:
                raise AuthorizationError(f"Access denied {remote_image.url}") from error
            raise  # pragma: no cover
        self._tick_progress()

        async for obj in stream:
            self._tick_progress()
            if "error" in obj.keys():
                self._end_progress()
                error_details = obj.get("errorDetail", {"message": "Unknown error"})
                raise DockerError(STATUS_CUSTOM_ERROR, error_details)
        self._tick_progress()

        await self._client.images.tag(repo, local_image.local)
        self._end_progress()

        print(f"Image {remote_image.url} pulled as " f"{local_image.local}")
        return local_image.local
