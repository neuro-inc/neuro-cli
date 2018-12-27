from dataclasses import dataclass
from typing import Any, Dict, Optional

from yarl import URL

from .api import API
from .jobs import (
    Container,
    Image,
    JobStatus,
    NetworkPortForwarding,
    Resources,
    network_to_api,
)


@dataclass(frozen=True)
class TrainResult:
    id: str
    status: JobStatus
    is_preemptible: bool
    http_url: URL = URL()
    internal_hostname: str = ""

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "TrainResult":
        return TrainResult(
            id=data["job_id"],
            status=JobStatus(data["status"]),
            is_preemptible=data["is_preemptible"],
            http_url=URL(data.get("http_url", "")),
            internal_hostname=data.get("internal_hostname", ""),
        )


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
        is_preemptible: bool = True,
    ) -> TrainResult:
        http, ssh = network_to_api(network)

        container = Container(
            image=image.image,
            command=image.command,
            http=http,
            ssh=ssh,
            resources=resources,
        )

        payload = {
            "container": container.to_api(),
            "dataset_storage_uri": str(dataset),
            "result_storage_uri": str(results),
            "is_preemptible": is_preemptible,
        }
        if description:
            payload["description"] = description

        url = URL(f"models")
        async with self._api.request("POST", url, json=payload) as resp:
            ret = await resp.json()
            return TrainResult.from_api(ret)
