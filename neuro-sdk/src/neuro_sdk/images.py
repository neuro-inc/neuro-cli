import contextlib
import logging
import re
from dataclasses import replace
from typing import Any, Dict, List, Optional, Set

import aiodocker
import aiohttp
from aiodocker.exceptions import DockerError
from yarl import URL

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
from .core import _Core
from .errors import AuthorizationError
from .parser import Parser
from .parsing_utils import LocalImage, RemoteImage, Tag, TagOption, _as_repo_str
from .utils import NoPublicConstructor, aclosing

REPOS_PER_PAGE = 30
TAGS_PER_PAGE = 30

log = logging.getLogger(__name__)


class Images(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: Config, parse: Parser) -> None:
        self._core = core
        self._config = config
        self._parse = parse
        self._temporary_images: Set[str] = set()
        self.__docker: Optional[aiodocker.Docker] = None

    def _get_image_url(self, remote: RemoteImage) -> URL:
        cluster_name = remote.cluster_name
        if cluster_name:
            assert remote.owner
            registry_url = self._config.get_cluster(cluster_name).registry_url
        else:
            registry_url = self._config.registry_url
        return registry_url.with_path("/v2/") / f"{remote.owner}/{remote.name}"

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
            async with aclosing(
                self._docker.images.push(repo, auth=auth, stream=True)
            ) as it:
                async for obj in it:
                    step = _try_parse_image_progress_step(obj, remote.tag)
                    if step:
                        progress.step(step)
        except DockerError as error:
            # TODO check this part when registry fixed
            if error.status == 403:
                raise AuthorizationError(f"Access denied {remote}") from error
            raise  # pragma: no cover
        return remote

    async def digest(self, remote: RemoteImage) -> str:
        auth = await self._config._registry_auth()
        assert remote.tag
        url = self._get_image_url(remote) / "manifests" / remote.tag
        async with self._core.request(
            "HEAD",
            url,
            auth=auth,
            headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"},
        ) as resp:
            return resp.headers["Docker-Content-Digest"]

    async def size(self, remote: RemoteImage) -> int:
        tag_information = await self.tag_info(remote)
        assert tag_information.size
        return tag_information.size

    async def tag_info(self, remote: RemoteImage) -> Tag:
        auth = await self._config._registry_auth()
        assert remote.tag
        url = self._get_image_url(remote) / "manifests" / remote.tag
        async with self._core.request(
            "GET",
            url,
            auth=auth,
            headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"},
        ) as resp:
            data = await resp.json()
            size = sum(layer["size"] for layer in data["layers"])
            return Tag(name=remote.tag, size=size)

    async def rm(self, remote: RemoteImage, digest: str) -> None:
        auth = await self._config._registry_auth()
        url = self._get_image_url(remote) / "manifests" / digest
        async with self._core.request("DELETE", url, auth=auth) as resp:
            assert resp

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
            async with aclosing(
                self._docker.pull(repo, auth=auth, repo=repo, stream=True)
            ) as it:
                async for obj in it:
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

    async def ls(self, cluster_name: Optional[str] = None) -> List[RemoteImage]:
        auth = await self._config._registry_auth()
        if cluster_name is None:
            cluster_name = self._config.cluster_name
        prefix = f"image://{cluster_name}/"
        url = self._config.get_cluster(cluster_name).registry_url
        url = url.with_path("/v2/") / "_catalog"
        result: List[RemoteImage] = []
        while True:
            url = url.update_query(n=str(REPOS_PER_PAGE))
            async with self._core.request("GET", url, auth=auth) as resp:
                ret = await resp.json()
                repos = ret["repositories"]
                for repo in repos:
                    try:
                        result.append(
                            self._parse.remote_image(
                                prefix + repo, tag_option=TagOption.DENY
                            )
                        )
                    except ValueError as err:
                        log.warning(str(err))
                if not repos or "next" not in resp.links:
                    break
                url = URL(resp.links["next"]["url"])
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
        auth = await self._config._registry_auth()
        url = self._get_image_url(image) / "tags" / "list"
        result: List[RemoteImage] = []
        while True:
            url = url.update_query(n=str(TAGS_PER_PAGE))
            async with self._core.request("GET", url, auth=auth) as resp:
                ret = await resp.json()
                tags = ret.get("tags", [])
                for tag in tags:
                    result.append(replace(image, tag=tag))
                if not tags or "next" not in resp.links:
                    break
                url = URL(resp.links["next"]["url"])
        return result


def _try_parse_image_progress_step(
    obj: Dict[str, Any], target_image_tag: Optional[str]
) -> Optional[ImageProgressStep]:
    _raise_on_error_chunk(obj)
    if "id" in obj and obj["id"] != target_image_tag:
        progress = obj.get("progress")
        detail = obj.get("progressDetail")

        if progress is not None:
            message = f"{obj['id']}: {obj['status']} {obj['progress']}"
        else:
            message = f"{obj['id']}: {obj['status']}"

        if detail is not None:
            current = detail.get("current")
            total = detail.get("total")
        else:
            current = total = None

        return ImageProgressStep(message, obj["id"], obj["status"], current, total)
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
