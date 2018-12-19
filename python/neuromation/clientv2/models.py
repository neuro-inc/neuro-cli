from typing import Optional

from yarl import URL

from neuromation.client.jobs import (
    Image,
    NetworkPortForwarding,
    Resources,
    network_to_api,
)
from neuromation.client.requests import ContainerPayload, ResourcesPayload
from neuromation.strings import parse

from .api import API
from .jobs import JobDescription


class Models:
    def __init__(self, api: API) -> None:
        self._api = api

    async def train(
        self,
        *,
        image: Image,
        resources: Resources,
        dataset: URL,
        results: URL,
        description: Optional[str] = None,
        network: Optional[NetworkPortForwarding] = None,
    ) -> JobDescription:
        http, ssh = network_to_api(network)

        container = ContainerPayload(
            image=image.image,
            command=image.command,
            http=http,
            ssh=ssh,
            resources=ResourcesPayload(
                memory_mb=parse.to_megabytes_str(resources.memory),
                cpu=resources.cpu,
                gpu=resources.gpu,
                gpu_model=resources.gpu_model,
                shm=resources.shm,
            ),
        )
        payload = {
            "container": container.to_primitive(),
            "dataset_storage_uri": str(dataset),
            "result_storage_uri": str(results),
        }
        if description:
            payload["description"] = description

        url = URL(f"models")
        async with self._api.request("POST", url, json=payload) as resp:
            ret = await resp.json()
            return JobDescription.from_api(ret)
