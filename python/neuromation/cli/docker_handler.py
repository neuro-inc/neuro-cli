from typing import Dict

import aiodocker
from aiodocker.exceptions import DockerError
from yarl import URL


STATUS_NOT_FOUND = 404
STATUS_CUSTOM_ERROR = 900


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

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.close()

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

    async def push(self, image_name: str) -> str:
        image, tag = self._split_tagged_image_name(image_name)
        repo = f"{self._registry.host}/{self._username}/{image}"

        print(f"Tagging {image_name} as {repo}")
        try:
            await self._client.images.tag(image, repo, tag=tag)
        except DockerError as error:
            if error.status == STATUS_NOT_FOUND:
                raise ValueError(
                    f"Image {image_name} not found in your local docker images"
                ) from error
            raise

        print(f"Pushing {repo}")
        stream = await self._client.images.push(
            repo, auth=self._auth(), tag=tag, stream=True
        )
        progress = "|\\-/"
        cnt = 0
        async for obj in stream:
            if "error" in obj.keys():
                error_details = obj.get("errorDetail", {"message": "Unknown error"})
                raise DockerError(STATUS_CUSTOM_ERROR, error_details)
            cnt = (cnt + 1) % len(progress)
            print(f"\r{progress[cnt]}", end="")
        print(f"\rImage {image_name} pushed to registry")

    async def pull(self, image_name: str) -> str:
        image, tag = self._split_tagged_image_name(image_name)
        repo = f"{self._registry.host}/{self._username}/{image}"
        print(f"Pulling {repo}")
        stream = await self._client.pull(
            repo, auth=self._auth(), tag=tag, repo=image, stream=True
        )
        progress = "|\\-/"
        cnt = 0
        async for obj in stream:
            if "error" in obj.keys():
                error_details = obj.get("errorDetail", {"message": "Unknown error"})
                raise DockerError(STATUS_CUSTOM_ERROR, error_details)
            cnt = (cnt + 1) % len(progress)
            print(f"\r{progress[cnt]}", end="")
        print(f"Image {image_name} pulled")

    async def close(self):
        await self._client.close()
