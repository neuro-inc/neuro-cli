import contextlib
import logging
import re
from dataclasses import replace
from typing import Any, Dict, List, Optional, Set

import aiodocker
import aiohttp
from aiodocker.exceptions import DockerError

from .abc import (
    AbstractDockerImageProgress,
    ImageCommitFinished,
    ImageCommitStarted,
    ImageProgressPull,
    ImageProgressPush,
    ImageProgressSave,
    ImageProgressStep,
)
from .config import Config
from .core import AuthorizationError, _Core
from .parser import Parser
from .parsing_utils import LocalImage, RemoteImage, TagOption, _as_repo_str
from .utils import NoPublicConstructor


log = logging.getLogger(__name__)


class Images(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: Config, parse: Parser) -> None:
        self._core = core
        self._config = config
        self._parse = parse
        self._temporary_images: Set[str] = set()
        self.__docker: Optional[aiodocker.Docker] = None
        self._registry_url = self._config.registry_url.with_path("/v2/")

    @property
    def _docker(self) -> aiodocker.Docker:
        if not self.__docker:
            try:
                self.__docker = aiodocker.Docker()
            except ValueError as error:
                if re.match(
                    r".*Either DOCKER_HOST or local sockets are not available.*",
                    f"{error}",
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
        return self.__docker

    async def _close(self) -> None:
        for image in self._temporary_images:
            with contextlib.suppress(DockerError, aiohttp.ClientError):
                await self._docker.images.delete(image)
        if self.__docker is not None:
            await self.__docker.close()

    async def push(
        self,
        local: LocalImage,
        remote: Optional[RemoteImage] = None,
        *,
        progress: Optional[AbstractDockerImageProgress] = None,
    ) -> RemoteImage:
        if remote is None:
            remote = self._parse._local_to_remote_image(local)

        if progress is None:
            progress = _DummyProgress()
        progress.push(ImageProgressPush(local, remote))

        repo = _as_repo_str(remote)
        try:
            await self._docker.images.tag(str(local), repo)
        except DockerError as error:
            if error.status == 404:
                raise ValueError(
                    f"Image {local} was not found " "in your local docker images"
                ) from error
        auth = await self._config._docker_auth()
        try:
            async for obj in self._docker.images.push(repo, auth=auth, stream=True):
                step = _try_parse_image_progress_step(obj, remote.tag)
                if step:
                    progress.step(step)
        except DockerError as error:
            # TODO check this part when registry fixed
            if error.status == 403:
                raise AuthorizationError(f"Access denied {remote}") from error
            raise  # pragma: no cover
        return remote

    async def pull(
        self,
        remote: RemoteImage,
        local: Optional[LocalImage] = None,
        *,
        progress: Optional[AbstractDockerImageProgress] = None,
    ) -> LocalImage:
        if local is None:
            local = self._parse._remote_to_local_image(remote)

        if progress is None:
            progress = _DummyProgress()
        progress.pull(ImageProgressPull(remote, local))

        repo = _as_repo_str(remote)
        auth = await self._config._docker_auth()
        try:
            async for obj in self._docker.pull(repo, auth=auth, repo=repo, stream=True):
                self._temporary_images.add(repo)
                step = _try_parse_image_progress_step(obj, remote.tag)
                if step:
                    progress.step(step)
        except DockerError as error:
            if error.status == 404:
                raise ValueError(
                    f"Image {remote} was not found " "in registry"
                ) from error
            # TODO check this part when registry fixed
            elif error.status == 403:
                raise AuthorizationError(f"Access denied {remote}") from error
            raise  # pragma: no cover

        await self._docker.images.tag(repo, str(local))

        return local

    async def ls(self) -> List[RemoteImage]:
        auth = await self._config._registry_auth()
        async with self._core.request(
            "GET", self._registry_url / "_catalog", auth=auth
        ) as resp:
            ret = await resp.json()
            prefix = f"image://{self._config.cluster_name}/"
            result: List[RemoteImage] = []
            for repo in ret["repositories"]:
                try:
                    result.append(
                        self._parse.remote_image(
                            prefix + repo, tag_option=TagOption.DENY
                        )
                    )
                except ValueError as err:
                    log.warning(str(err))
            return result

    def _validate_image_for_tags(self, image: RemoteImage) -> None:
        err = f"Invalid image `{image}`: "
        if image.tag is not None:
            raise ValueError(err + "tag is not allowed")
        if not image.owner:
            raise ValueError(err + "missing image owner")
        if not image.name:
            raise ValueError(err + "missing image name")

    async def tags(self, image: RemoteImage) -> List[RemoteImage]:
        self._validate_image_for_tags(image)
        name = f"{image.owner}/{image.name}"
        auth = await self._config._registry_auth()
        async with self._core.request(
            "GET", self._registry_url / name / "tags" / "list", auth=auth
        ) as resp:
            ret = await resp.json()
            return [replace(image, tag=tag) for tag in ret.get("tags", [])]


def _try_parse_image_progress_step(
    obj: Dict[str, Any], target_image_tag: Optional[str]
) -> Optional[ImageProgressStep]:
    _raise_on_error_chunk(obj)
    if "id" in obj.keys() and obj["id"] != target_image_tag:
        if "progress" in obj.keys():
            message = f"{obj['id']}: {obj['status']} {obj['progress']}"
        else:
            message = f"{obj['id']}: {obj['status']}"
        return ImageProgressStep(message, obj["id"])
    return None


def _raise_on_error_chunk(obj: Dict[str, Any]) -> None:
    if "error" in obj.keys():
        error_details = obj.get("errorDetail", {"message": "Unknown error"})
        raise DockerError(900, error_details)


class _DummyProgress(AbstractDockerImageProgress):
    def pull(self, data: ImageProgressPull) -> None:
        pass

    def push(self, data: ImageProgressPush) -> None:
        pass

    def step(self, data: ImageProgressStep) -> None:
        pass

    def save(self, data: ImageProgressSave) -> None:
        pass

    def commit_started(self, data: ImageCommitStarted) -> None:
        pass

    def commit_finished(self, data: ImageCommitFinished) -> None:
        pass
