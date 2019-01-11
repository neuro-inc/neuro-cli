from typing import Dict, List

import aiodocker
from aiodocker.exceptions import DockerError
from yarl import URL
from dataclasses import dataclass

STATUS_NOT_FOUND = 404
STATUS_CUSTOM_ERROR = 900


@dataclass()
class ImageInfo:
    name: str
    tag: str = 'latest'
    username: str = None

    @classmethod
    def from_local_image_name(cls, image_name: str) -> "ImageInfo":
        colon_count = image_name.count(":")
        if colon_count == 0:
            return ImageInfo(name=image_name)
        if colon_count == 1:
            name, tag = image_name.split(":")
            if name:
                return ImageInfo(name=name, tag=tag)
        raise ValueError(f"Invalid image name format: {image_name}")

    @classmethod
    def from_remote_image_name(cls, image_name: str) -> "ImageInfo":
        if image_name.count('/'):
            username, name = image_name.split('/', 2)
            info = ImageInfo.from_local_image_name(image_name)
            return ImageInfo(username=username, name=info.name, tag=info.tag)
        else:
            return ImageInfo.from_local_image_name(image_name)

    @classmethod
    def from_url(cls, url: URL) -> "ImageInfo":
        if url.scheme != 'image':
            raise ValueError(f"Invalid scheme, for image name : {url}")
        return cls.from_remote_image_name(url.path)

    def to_local_image_name(self) -> str:
        return f"{self.name}:{self.tag}"

    def to_remote_image_name(self) -> str:
        if not self.username:
            raise Exception('User is not specified')
        return f"{self.username}/{self.name}:{self.tag}"

    def to_url(self) -> URL:
        return URL(f'image://{self.to_remote_image_name()}')


@dataclass()
class ImageMapping:
    local: ImageInfo
    remote: ImageInfo


class DockerHandler:
    """
    Docker-related manipulation handler
    At this moment image/registry  manipulations available
    """

    def __init__(self, username: str, token: str, registry: URL) -> None:
        self._username = username
        self._token = token
        self._registry = registry
        self._client = aiodocker.Docker()
        self._temporary_images = list()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            for image in self._temporary_images:
                    await self._client.images.delete(image)
            await self._client.close()
        except BaseException:
            # Just ignore any error
            pass

    def _auth(self) -> Dict[str, str]:
        return {"username": "token", "password": self._token}

    @classmethod
    def _split_tagged_image_name(cls, image_name: str):
        colon_count = image_name.count(":")
        if colon_count == 0:
            return image_name, "latest"
        if colon_count == 1:
            name, tag = image_name.split(":")
            if name:
                return name, tag
        raise ValueError(f"Invalid image name format: {image_name}")

    async def push(self, image_name: str, remote_image_name: str) -> URL:
        local_image = ImageInfo.from_local_image_name(image_name)
        if remote_image_name:
            remote_image = ImageInfo.from_remote_image_name(remote_image_name)
            if not remote_image.username:
                remote_image = ImageInfo(username=self._username,
                                         name=remote_image.name,
                                         tag=remote_image.tag)
        else:
            remote_image = ImageInfo(username=self._username,
                                     name=local_image.name, tag=local_image.tag)

        repo = f"{self._registry.host}/{remote_image.to_remote_image_name()}"

        try:
            await self._client.images.tag(local_image.name, repo,
                                          tag=local_image.tag)
            self._temporary_images.append(repo)
        except DockerError as error:
            if error.status == STATUS_NOT_FOUND:
                raise ValueError(
                    f"Image {local_image_name} not found in your local docker images"
                ) from error
            raise
        stream = await self._client.images.push(
            repo, auth=self._auth(), stream=True
        )
        progress = "|\\-/"
        cnt = 0
        async for obj in stream:
            if "error" in obj.keys():
                error_details = obj.get("errorDetail",
                                        {"message": "Unknown error"})
                raise DockerError(STATUS_CUSTOM_ERROR, error_details)
            cnt = (cnt + 1) % len(progress)
            print(f"\r{progress[cnt]}", end="")
        print(
            f"\rImage {image_name} pushed to registry as {remote_image.to_url()}")
        return remote_image.to_url()

    async def pull(self, image_name: str, local_image_name: str) -> str:
        remote_image = ImageInfo.from_remote_image_name(image_name)
        if not remote_image.username:
            remote_image = ImageInfo(username=self._username,
                                     name=remote_image.name,
                                     tag=remote_image.tag)
        if local_image_name:
            local_image = ImageInfo.from_local_image_name(local_image_name)
        else:
            local_image = ImageInfo(name=remote_image.name,
                                    tag=remote_image.tag)

        repo = f"{self._registry.host}/{remote_image.to_remote_image_name()}"
        stream = await self._client.pull(
            repo, auth=self._auth(), repo=repo, stream=True
        )
        progress = "|\\-/"
        cnt = 0
        async for obj in stream:
            if "error" in obj.keys():
                error_details = obj.get("errorDetail",
                                        {"message": "Unknown error"})
                raise DockerError(STATUS_CUSTOM_ERROR, error_details)
            elif "progress" in obj.keys():
                print(f"\r{obj['status']} {obj['progress']}", end="")
            else:
                cnt = (cnt + 1) % len(progress)
                print(f"\r{progress[cnt]}", end="")
        self._temporary_images.append(repo)
        print(f"\rTagging pulled image ...", end="")
        await self._client.images.tag(repo, local_image.to_local_image_name())
        print(f"\rImage {remote_image.to_url()} pulled as {local_image.to_local_image_name()}")
        return local_image.to_local_image_name()
