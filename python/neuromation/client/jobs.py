import asyncio
import enum
from dataclasses import dataclass
from io import BufferedReader
from typing import Any, AsyncIterable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from async_generator import asynccontextmanager

from neuromation.http.fetch import FetchError
from neuromation.strings import parse

from .client import ApiClient
from .requests import (
    ContainerPayload,
    InferRequest,
    JobKillRequest,
    JobListRequest,
    JobMonitorRequest,
    JobStatusRequest,
    JobSubmissionRequest,
    ResourcesPayload,
    ShareResourceRequest,
    TrainRequest,
    VolumeDescriptionPayload,
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

    async def wait(self, timeout: Optional[float] = None) -> "JobItem":
        try:
            return await asyncio.wait_for(self._call(), timeout=timeout)
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


class ResourceSharing(ApiClient):
    async def share(self, path: str, action: str, whom: str) -> bool:
        permissions = [{"uri": path, "action": action}]
        await self._fetch(ShareResourceRequest(whom, permissions))
        return True


class Model(ApiClient):
    async def infer(
        self,
        *,
        image: Image,
        resources: Resources,
        network: Optional[NetworkPortForwarding],
        model: str,
        dataset: str,
        results: str,
        description: Optional[str],
    ) -> JobItem:
        http, ssh = network_to_api(network)
        res = await self._fetch(
            InferRequest(
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
                model_storage_uri=model,
                dataset_storage_uri=dataset,
                result_storage_uri=results,
                description=description,
            )
        )

        return JobItem(
            id=res["job_id"], status=res["status"], client=self, description=description
        )

    async def train(
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
        res = await self._fetch(
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


class Job(ApiClient):
    async def submit(
        self,
        *,
        image: Image,
        resources: Resources,
        network: NetworkPortForwarding,
        volumes: Optional[List[VolumeDescriptionPayload]],
        description: Optional[str],
    ) -> JobDescription:
        http, ssh = network_to_api(network)
        resources_payload: ResourcesPayload = ResourcesPayload(
            memory_mb=parse.to_megabytes_str(resources.memory),
            cpu=resources.cpu,
            gpu=resources.gpu,
            gpu_model=resources.gpu_model,
            shm=resources.shm,
        )
        container = ContainerPayload(
            image=image.image,
            command=image.command,
            http=http,
            ssh=ssh,
            resources=resources_payload,
        )
        res = await self._fetch(
            JobSubmissionRequest(
                container=container, volumes=volumes, description=description
            )
        )

        return self._dict_to_description(res)

    async def list(self) -> List[JobDescription]:
        res = await self._fetch(JobListRequest())
        return [self._dict_to_description_with_history(job) for job in res["jobs"]]

    async def kill(self, id: str) -> bool:
        await self._fetch(JobKillRequest(id=id))
        # TODO(artyom, 07/16/2018): what are we returning here?
        return True

    @asynccontextmanager
    async def monitor(self, id: str) -> AsyncIterable[BufferedReader]:
        try:
            job_ctx = await self._fetch(JobMonitorRequest(id=id))
            async with job_ctx as content:
                yield content
        except FetchError as error:
            error_class = type(error)
            mapped_class = self._exception_map.get(error_class, error_class)
            raise mapped_class(error) from error

    async def status(self, id: str) -> JobDescription:
        res = await self._fetch(JobStatusRequest(id=id))
        return self._dict_to_description_with_history(res)

    def _dict_to_description_with_history(self, res: Dict[str, Any]) -> JobDescription:
        job_description = self._dict_to_description(res)
        job_history = None
        if "history" in res:
            job_history = JobStatusHistory(
                status=res["history"].get("status", None),
                reason=res["history"].get("reason", None),
                description=res["history"].get("description", None),
                created_at=res["history"].get("created_at", None),
                started_at=res["history"].get("started_at", None),
                finished_at=res["history"].get("finished_at", None),
            )
        return JobDescription(
            client=self,
            id=job_description.id,
            status=job_description.status,
            image=job_description.image,
            command=job_description.command,
            history=job_history,
            resources=job_description.resources,
            url=job_description.url,
            ssh=job_description.ssh,
            owner=job_description.owner,
            description=job_description.description,
        )

    def _dict_to_description(self, res: Dict[str, Any]) -> JobDescription:
        job_container_image = None
        job_command = None
        job_resources = None

        if "container" in res:
            job_container_image = (
                res["container"]["image"] if "image" in res["container"] else None
            )
            job_command = (
                res["container"]["command"] if "command" in res["container"] else None
            )

            if "resources" in res["container"]:
                container_resources = res["container"]["resources"]
                shm = container_resources.get("shm", None)
                gpu = container_resources.get("gpu", None)
                gpu_model = container_resources.get("gpu_model", None)
                job_resources = Resources(
                    cpu=container_resources["cpu"],
                    memory=container_resources["memory_mb"],
                    gpu=gpu,
                    shm=shm,
                    gpu_model=gpu_model,
                )
        http_url = res.get("http_url", "")
        ssh_conn = res.get("ssh_server", "")
        description = res.get("description")
        job_owner = res.get("owner", "")
        return JobDescription(
            client=self,
            id=res["id"],
            status=res["status"],
            image=job_container_image,
            command=job_command,
            resources=job_resources,
            url=http_url,
            ssh=ssh_conn,
            owner=job_owner,
            description=description,
        )
