import enum
import re
from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List, Optional, SupportsInt, Tuple
from urllib.parse import urlparse

from yarl import URL

from neuromation.strings import parse

from .api import API


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


@dataclass
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

    _image_re: ClassVar[Any] = re.compile(
        r"^((?P<home>~/)|(((?P<repo>[^/]+)/)?(?P<uname>[^/]+)/))?"
        r"(?P<img>[^/:]+)(:(?P<tag>[^/:]+))?$"
    )

    @classmethod
    def parse_image_name(
        cls, image_name: str, default_repo: str, default_user_name: str
    ):
        match = cls._image_re.match(image_name)
        if match is None:
            raise ValueError(
                f"Invalid image name '{image_name}': "
                f"does not match pattern {cls._image_re}"
            )
        img = match.group("img")
        assert img
        tag = match.group("tag") or "latest"

        repo, uname = match.group("repo"), match.group("uname")
        if not repo:
            home = match.group("home")
            if home:
                repo, uname = default_repo, default_user_name
            else:
                repo = "docker.io"
                if not uname:
                    uname = "library"
        return f"{repo}/{uname}/{img}:{tag}"


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


@dataclass(frozen=True)
class ResourcesPayload:
    memory_mb: str
    cpu: float
    gpu: Optional[int]
    gpu_model: Optional[str]
    shm: Optional[bool]

    def to_primitive(self) -> Dict[str, Any]:
        value = {"memory_mb": self.memory_mb, "cpu": self.cpu, "shm": self.shm}
        if self.gpu:
            value["gpu"] = self.gpu
            value["gpu_model"] = self.gpu_model
        return value


@dataclass(frozen=True)
class ContainerPayload:
    image: str
    command: Optional[str]
    http: Optional[Dict[str, int]]
    ssh: Optional[Dict[str, int]]
    resources: ResourcesPayload
    env: Optional[Dict[str, str]] = None

    def to_primitive(self) -> Dict[str, Any]:
        primitive = {"image": self.image, "resources": self.resources.to_primitive()}
        if self.command:
            primitive["command"] = self.command
        if self.http:
            primitive["http"] = self.http
        if self.ssh:
            primitive["ssh"] = self.ssh
        if self.env:
            primitive["env"] = self.env
        return primitive


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
    owner: str
    history: JobStatusHistory
    resources: Resources
    is_preemptible: bool
    description: Optional[str] = None
    command: Optional[str] = None
    url: URL = URL()
    ssh: URL = URL()
    env: Optional[Dict[str, str]] = None

    def jump_host(self) -> Optional[str]:
        ssh_hostname = self.ssh.host
        if ssh_hostname is None:
            return None
        ssh_hostname = ".".join(ssh_hostname.split(".")[1:])
        return ssh_hostname

    @classmethod
    def from_api(cls, res: Dict[str, Any]) -> "JobDescription":
        job_container_image = res["container"]["image"]
        job_command = res["container"].get("command", None)
        job_env = res["container"].get("env", None)

        job_owner = res["owner"]
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
        http_url = URL(res.get("http_url", ""))
        ssh_conn = URL(res.get("ssh_server", ""))
        description = res.get("description", None)
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
        payload: Dict[str, Any] = {"container": container.to_primitive()}
        if volumes:
            prim_volumes = [v.to_primitive() for v in volumes]
        else:
            prim_volumes = []
        payload["container"]["volumes"] = prim_volumes
        if description:
            payload["description"] = description
        if is_preemptible is not None:
            payload["is_preemptible"] = is_preemptible
        async with self._api.request("POST", url, json=payload) as resp:
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
