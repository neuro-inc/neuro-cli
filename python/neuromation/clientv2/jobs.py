from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from yarl import URL

from neuromation.client.jobs import (
    Image,
    JobStatus,
    NetworkPortForwarding,
    Resources,
    network_to_api,
)
from neuromation.client.requests import ContainerPayload, ResourcesPayload
from neuromation.strings import parse

from .api import API


@dataclass(frozen=True)
class VolumeDescriptionPayload:
    storage_path: str
    container_path: str
    read_only: bool

    def to_primitive(self) -> Dict[str, Any]:
        resp: Dict[str, Any] = {
            "src_storage_uri": self.storage_path,
            "dst_path": self.container_path,
        }
        if self.read_only:
            resp["read_only"] = bool(self.read_only)
        else:
            resp["read_only"] = False
        return resp

    @classmethod
    def from_cli(cls, username: str, volume: str) -> "VolumeDescriptionPayload":
        volume_desc_parts = volume.split(":")
        if len(volume_desc_parts) != 3 and len(volume_desc_parts) != 4:
            raise ValueError(f"Invalid volume specification '{volume}'")

        storage_path = ":".join(volume_desc_parts[:-1])
        container_path = volume_desc_parts[2]
        read_only = False
        if len(volume_desc_parts) == 4:
            if not volume_desc_parts[-1] in ["ro", "rw"]:
                raise ValueError(f"Wrong ReadWrite/ReadOnly mode spec for '{volume}'")
            read_only = volume_desc_parts[-1] == "ro"
            storage_path = ":".join(volume_desc_parts[:-2])

        # TODO: Refactor PlatformStorageOperation tight coupling
        from neuromation.cli.command_handlers import PlatformStorageOperation

        pso = PlatformStorageOperation(username)
        pso._is_storage_path_url(urlparse(storage_path, scheme="file"))
        storage_path_with_principal = (
            f"storage:/{str(pso.render_uri_path_with_principal(storage_path))}"
        )

        return VolumeDescriptionPayload(
            storage_path_with_principal, container_path, read_only
        )

    @classmethod
    def from_cli_list(
        cls, username: str, lst: List[str]
    ) -> Optional[List["VolumeDescriptionPayload"]]:
        if not lst:
            return None
        return [cls.from_cli(username, s) for s in lst]


@dataclass(frozen=True)
class JobStatusHistory:
    status: JobStatus
    reason: str
    description: str
    created_at: str
    started_at: str
    finished_at: str


@dataclass(frozen=True)
class JobDescription:
    status: JobStatus
    id: str
    image: str
    command: str
    owner: str
    history: JobStatusHistory
    description: str
    resources: Resources
    is_preemptible: bool
    url: URL = URL()
    ssh: URL = URL()
    env: Optional[Dict[str, str]] = None

    def jump_host(self) -> str:
        ssh_hostname = self.ssh.host
        assert ssh_hostname is not None
        ssh_hostname = ".".join(ssh_hostname.split(".")[1:])
        return ssh_hostname

    @classmethod
    def from_api(cls, res: Dict[str, Any]) -> "JobDescription":
        job_container_image = res["container"]["image"]
        job_command = res["container"]["command"]
        job_env = res["container"].get("env", None)

        job_owner = res["owner"]
        container_resources = res["container"]["resources"]
        shm = container_resources.get("shm", None)
        gpu = container_resources["gpu"]
        gpu_model = container_resources.get("gpu_model", None)

        job_resources = Resources(
            cpu=container_resources["cpu"],
            memory=container_resources["memory_mb"],
            gpu=gpu,
            shm=shm,
            gpu_model=gpu_model,
        )
        http_url = URL(res.get("http_url", ""))
        ssh_conn = URL(res.get("ssh_server", ""))
        description = res.get("description", "")
        job_history = JobStatusHistory(
            status=JobStatus(res["history"].get("status", "unknown")),
            reason=res["history"].get("reason", ""),
            description=res["history"].get("description", ""),
            created_at=res["history"].get("created_at", ""),
            started_at=res["history"].get("started_at", ""),
            finished_at=res["history"].get("finished_at", ""),
        )
        return JobDescription(
            id=res["id"],
            status=JobStatus(res["status"]),
            image=job_container_image,
            command=job_command,
            resources=job_resources,
            history=job_history,
            url=http_url,
            ssh=ssh_conn,
            owner=job_owner,
            description=description,
            env=job_env,
            is_preemptible=res["is_preemptible"],
        )


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
        is_preemptible: bool = False,
        env: Optional[Dict[str, str]] = None,
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
            env=env,
        )

        url = URL("jobs")
        request_details: Dict[str, Any] = {"container": container.to_primitive()}
        if volumes:
            prim_volumes = [v.to_primitive() for v in volumes]
        else:
            prim_volumes = []
        request_details["container"]["volumes"] = prim_volumes
        if description:
            request_details["description"] = description
        if is_preemptible is not None:
            request_details["is_preemptible"] = is_preemptible
        async with self._api.request("POST", url, json=request_details) as resp:
            res = await resp.json()
            return JobDescription.from_api(res)

    async def list(self) -> List[JobDescription]:
        url = URL(f"jobs")
        async with self._api.request("GET", url) as resp:
            ret = await resp.json()
            return [JobDescription.from_api(j) for j in ret["jobs"]]

    async def kill(self, id: str) -> None:
        url = URL(f"jobs/{id}")
        async with self._api.request("DELETE", url):
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

    async def status(self, id: str) -> JobDescription:
        url = URL(f"jobs/{id}")
        async with self._api.request("GET", url) as resp:
            ret = await resp.json()
            return JobDescription.from_api(ret)
