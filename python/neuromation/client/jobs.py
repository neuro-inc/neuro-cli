import asyncio
import enum
from dataclasses import dataclass
from typing import Dict, Optional, SupportsInt, Tuple
from urllib.parse import urlparse

from neuromation.strings import parse

from .client import ApiClient
from .requests import (
    ContainerPayload,
    JobStatusRequest,
    ResourcesPayload,
    ShareResourceRequest,
    TrainRequest,
)


def network_to_api(
    network: Optional["NetworkPortForwarding"]
) -> Tuple[Optional[Dict[str, int]], Optional[Dict[str, int]]]:
    http = None
    ssh = None
    if network:
        if "http" in network.ports:
            http = {"port": network.ports["http"]}
        if "ssh" in network.ports:
            ssh = {"port": network.ports["ssh"]}
    return http, ssh


@dataclass(frozen=True)
class Resources:
    memory: str
    cpu: float
    gpu: Optional[int]
    shm: Optional[bool]
    gpu_model: Optional[str]

    @classmethod
    def create(
        cls, cpu: str, gpu: str, gpu_model: str, memory: str, extshm: str
    ) -> "Resources":
        return cls(memory, float(cpu), int(gpu), bool(extshm), gpu_model)


@dataclass()
class NetworkPortForwarding:
    ports: Dict[str, int]

    @classmethod
    def from_cli(
        cls, http: SupportsInt, ssh: SupportsInt
    ) -> Optional["NetworkPortForwarding"]:
        net = None
        ports: Dict[str, int] = {}
        if http:
            ports["http"] = int(http)
        if ssh:
            ports["ssh"] = int(ssh)
        if ports:
            net = NetworkPortForwarding(ports)
        return net


@dataclass(frozen=True)
class Image:
    image: str
    command: Optional[str]


@dataclass(frozen=True)
class JobStatusHistory:
    status: str
    reason: str
    description: str
    created_at: str
    started_at: str
    finished_at: str


@dataclass(frozen=True)
class JobDescription:
    status: str
    id: str
    client: ApiClient
    image: Optional[str] = None
    command: Optional[str] = None
    url: str = ""
    ssh: str = ""
    env: Optional[Dict[str, str]] = None
    owner: Optional[str] = None
    history: Optional[JobStatusHistory] = None
    resources: Optional[Resources] = None
    description: Optional[str] = None

    def jump_host(self) -> str:
        ssh_hostname = urlparse(self.ssh).hostname
        ssh_hostname = ".".join(ssh_hostname.split(".")[1:])
        return ssh_hostname


@dataclass(frozen=True)
class JobItem:
    status: str
    id: str
    client: ApiClient
    url: str = ""
    history: Optional[JobStatusHistory] = None
    description: Optional[str] = None

    async def _call(self) -> "JobItem":
        return JobItem(
            client=self.client,
            **await self.client._fetch(request=JobStatusRequest(id=self.id)),
        )

    def wait(self, timeout: Optional[float] = None) -> "JobItem":
        try:
            return self.client.loop.run_until_complete(
                asyncio.wait_for(self._call(), timeout=timeout)
            )
        except asyncio.TimeoutError:
            raise TimeoutError


class JobStatus(str, enum.Enum):
    """An Enum subclass that represents job statuses.
    PENDING: a job is being created and scheduled. This includes finding (and
    possibly waiting for) sufficient amount of resources, pulling an image
    from a registry etc.
    RUNNING: a job is being run.
    SUCCEEDED: a job terminated with the 0 exit code or a running job was
    manually terminated/deleted.
    FAILED: a job terminated with a non-0 exit code.
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNKNOWN = "unknown"  # invalid status code, a default value is status is not sent


class ResourceSharing(ApiClient):
    def share(self, path: str, action: str, whom: str) -> bool:
        permissions = [{"uri": path, "action": action}]
        self._fetch_sync(ShareResourceRequest(whom, permissions))
        return True


class Model(ApiClient):
    def train(
        self,
        *,
        image: Image,
        resources: Resources,
        network: Optional[NetworkPortForwarding],
        dataset: str,
        results: str,
        description: Optional[str],
    ) -> JobItem:
        http, ssh = network_to_api(network)
        res = self._fetch_sync(
            TrainRequest(
                container=ContainerPayload(
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
                ),
                dataset_storage_uri=dataset,
                result_storage_uri=results,
                description=description,
            )
        )

        return JobItem(
            id=res["job_id"], status=res["status"], client=self, description=description
        )
