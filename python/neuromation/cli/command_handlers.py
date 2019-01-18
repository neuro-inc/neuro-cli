import logging
import os
from pathlib import PosixPath, PurePosixPath
from typing import Dict
from urllib.parse import ParseResult, urlparse

import docker
from docker.errors import APIError


log = logging.getLogger(__name__)

BUFFER_SIZE_MB = 1

BUFFER_SIZE_B = BUFFER_SIZE_MB * 1024 * 1024

PLATFORM_DELIMITER = "/"

SYSTEM_PATH_DELIMITER = os.sep


class PlatformOperation:
    def __init__(self, principal: str, token: str) -> None:
        self._principal = principal
        self._token = token


class PlatformStorageOperation:
    def __init__(self, principal: str):
        self.principal = principal

    def _get_principal(self, path_url: ParseResult) -> str:
        path_principal = path_url.hostname
        if not path_principal:
            path_principal = self.principal
        if path_principal == "~":
            path_principal = self.principal
        return path_principal

    def _is_storage_path_url(self, path: ParseResult):
        if path.scheme != "storage":
            raise ValueError("Path should be targeting platform storage.")

    def _render_platform_path(self, path_str: str) -> PosixPath:
        target_path: PosixPath = PosixPath(path_str)
        if target_path.is_absolute():
            target_path = target_path.relative_to(PosixPath("/"))
        return target_path

    def _render_platform_path_with_principal(self, path: ParseResult) -> PosixPath:
        target_path: PosixPath = self._render_platform_path(path.path)
        target_principal = self._get_principal(path)
        posix_path = PurePosixPath(PLATFORM_DELIMITER, target_principal, target_path)
        return posix_path

    def render_uri_path_with_principal(self, path: str):
        # Special case that shall be handled here, when path is '//'
        if path == "storage://":
            return PosixPath(PLATFORM_DELIMITER)

        # Normal processing flow
        path_url = urlparse(path, scheme="file")
        self._is_storage_path_url(path_url)
        return self._render_platform_path_with_principal(path_url)


class DockerHandler(PlatformOperation):
    def __init__(self, principal: str, token: str) -> None:
        super().__init__(principal, token)
        self._client = docker.APIClient()

    def _is_docker_available(self) -> bool:
        try:
            self._client.ping()
            return True
        except APIError:
            return False

    def _auth(self) -> Dict[str, str]:
        return {"username": "token", "password": self._token}

    @classmethod
    def _split_tagged_image_name(cls, image_name: str):
        colon_count = image_name.count(":")
        if colon_count == 0:
            return image_name, ""
        if colon_count == 1:
            name, tag = image_name.split(":")
            if name:
                return name, tag
        raise ValueError(f"Invalid image name format: {image_name}")

    def push(self, registry: str, image_name: str) -> str:
        if self._is_docker_available():
            try:
                image, tag = self._split_tagged_image_name(image_name)

                repository_url = f"{registry}/{self._principal}/{image}:{tag}"
                if not self._client.tag(image_name, repository_url, tag, force=True):
                    raise ValueError("Error tagging image.")
                progress = "|\\-/"
                cnt = 0
                for line in self._client.push(
                    repository_url,
                    stream=True,
                    decode=True,
                    tag=tag,
                    auth_config=self._auth(),
                ):  # pragma no cover
                    cnt = (cnt + 1) % len(progress)
                    print(f"\r{progress[cnt]}", end="")
                return repository_url
            except docker.errors.APIError as e:
                raise ValueError(
                    f"Cannot push container image to registry. Error {e.explanation}"
                ) from e

    def pull(self, registry: str, image_name: str) -> str:
        if self._is_docker_available():
            try:
                image, tag = self._split_tagged_image_name(image_name)

                repository_url = image
                progress = "|\\-/"
                cnt = 0
                for line in self._client.pull(
                    repository_url,
                    tag=tag,
                    stream=True,
                    decode=True,
                    auth_config=self._auth(),
                ):  # pragma no cover
                    cnt = (cnt + 1) % len(progress)
                    print(f"\r{progress[cnt]}", end="")
                return repository_url
            except docker.errors.APIError as e:
                log.error(e)
                raise ValueError(
                    f"Cannot pull container image from registry. Error {e.explanation}"
                ) from e
