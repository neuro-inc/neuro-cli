from typing import Any, List, Optional

from yarl import URL

from neuromation.client.jobs import (
    Image,
    JobDescription,
    NetworkPortForwarding,
    Resources,
    VolumeDescriptionPayload,
)

from .api import API


class Jobs:
    def __init__(self, api: API) -> None:
        self._api = api

    async def submit(
        self,
        *,
        image: Image,
        resources: Resources,
        network: NetworkPortForwarding,
        volumes: Optional[List[VolumeDescriptionPayload]],
        description: Optional[str],
        is_preemptible: Optional[bool] = False,
    ) -> JobDescription:
        raise NotImplementedError

    async def list(self) -> List[JobDescription]:
        raise NotImplementedError

    async def kill(self, id: str) -> str:
        """
        the method returns None when the server has responded
        with HTTPNoContent in case of successful job deletion,
        and the text response otherwise (possibly empty).
        """
        url = URL(f"jobs/{id}")
        async with self._api.request(
            "DELETE", url
        ):
            # an error is raised for status >= 400
            return None  # 201 status code

    async def monitor(
        self, id: str
    ) -> Any:  # real type is async generator with data chunks
        url = URL(f"jobs/{id}/log")
        async with self._api.request(
            "GET", url, headers={"Accept-Encoding": "identity"}
        ) as resp:
            async for data in resp.content.iter_any():
                yield data

    def status(self, id: str) -> JobDescription:
        raise NotImplementedError
