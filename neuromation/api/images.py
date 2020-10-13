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
from .core import _Core
from .errors import AuthorizationError
from .parser import Parser
from .parsing_utils import LocalImage, RemoteImage, TagOption, _as_repo_str
from .utils import NoPublicConstructor


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

    async def digest(self, remote: RemoteImage) -> str:
        name = f"{remote.owner}/{remote.name}"
        auth = await self._config._registry_auth()
        assert remote.tag
        url = self._registry_url / name / "manifests" / remote.tag
        async with self._core.request(
            "GET",
            url,
            auth=auth,
            headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"},
        ) as resp:
            """
            Sample response
            {
               "schemaVersion": 2,
               "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
               "config": {
                  "mediaType": "application/vnd.docker.container.image.v1+json",
                  "size": 10118,
                  "digest": "sha256:8d039ece80d31b10dde3c697d4ba03dabfc29d8664a2a6d4f9
               },
               "layers": [
                  {
                     "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                     "size": 45309934,
                     "digest": "sha256:bc9ab73e5b14b9fbd3687a4d8c1f1360533d6ee9ffc3f5e
                  },
                  {
                     "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                     "size": 10740016,
                     "digest": "sha256:193a6306c92af328dbd41bbbd3200a2c90802624cccfe57
                  },
                  {
                     "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                     "size": 4336053,
                     "digest": "sha256:e5c3f8c317dc30af45021092a3d76f16ba7aa1ee5f18fec
                  },
                  {
                     "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                     "size": 50065549,
                     "digest": "sha256:a587a86c9dcb9df6584180042becf21e36ecd8b460a7617
                  },
                  {
                     "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                     "size": 213202596,
                     "digest": "sha256:72744d0a318b0788001cc4f5f83c6847ba4b753307fadd0
                  },
                  {
                     "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                     "size": 5744764,
                     "digest": "sha256:6598fc9d11d10365ac9281071a87930a2382ee31d026f1b
                  },
                  {
                     "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                     "size": 20950985,
                     "digest": "sha256:4b1d9004d467b4e710d770a881df027df7e5e7e4629f6e4
                  },
                  {
                     "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                     "size": 240,
                     "digest": "sha256:93612f47cdc374d0b33057b9e71eac173ac469da3e1a631
                  },
                  {
                     "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                     "size": 1780802,
                     "digest": "sha256:1bc4b4b508703799ef67a807dacce4736045e642e87bcd4
                  },
                  {
                     "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                     "size": 100,
                     "digest": "sha256:0ddca6a54335adea4a2a50e7385a1e76519dd8b7ca32782
                  },
                  {
                     "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                     "size": 639,
                     "digest": "sha256:7dbf5167a7cb414d1becc6e42028bc34a8c265bf7755953
                  },
                  {
                     "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                     "size": 17613054,
                     "digest": "sha256:f62d7173e796ef811c6956b7295c4ccfb736eaf218bbad2
                  },
                  {
                     "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                     "size": 59011,
                     "digest": "sha256:d29fe402a3713516c8eedec84b9a94b65ba453a7f54e522
                  },
                  {
                     "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                     "size": 31358,
                     "digest": "sha256:4a7b15f8645bb72d23021d553c735c060930fb15dfd9266
                  },
                  {
                     "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                     "size": 1455,
                     "digest": "sha256:f6d54c29d93a51bd06fc73c714c2737ee73dea5f11e252d
                  },
                  {
                     "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                     "size": 686,
                     "digest": "sha256:faf3c662aed76d8ee8b857021dd48e287073fd8e7c2b4c8
                  },
                  {
                     "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                     "size": 459,
                     "digest": "sha256:b60b0cb6f684eafe3ab6d5ceb3694cc785fbf379eb76196
                  }
               ]
            }
            """
            ret = await resp.json()
            return ret["config"]["digest"]

    async def rm(self, remote: RemoteImage, digest: str) -> None:
        try:
            name = f"{remote.owner}/{remote.name}"
            auth = await self._config._registry_auth()
            url = self._registry_url / name / "manifests" / digest
            print(url)
            async with self._core.request("DELETE", url, auth=auth) as resp:
                assert resp
        except DockerError as error:
            if error.status == 404:
                raise ValueError(f"Image {remote} was not found") from error

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
        prefix = f"image://{self._config.cluster_name}/"
        url = self._registry_url / "_catalog"
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
                url = resp.links["next"]["url"]
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
        url = self._registry_url / name / "tags" / "list"
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
                url = resp.links["next"]["url"]
        return result


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
