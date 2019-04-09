import asyncio
import enum
import json
import shlex
from dataclasses import dataclass, field
from typing import (
    Any,
    AsyncIterator,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    SupportsInt,
    Tuple,
)

from aiohttp import WSServerHandshakeError
from multidict import MultiDict
from yarl import URL

from neuromation.utils import kill_proc_tree

from .core import Core, IllegalArgumentError
from .url_utils import normalize_storage_path_uri


@dataclass(frozen=True)
class Resources:
    memory_mb: str
    cpu: float
    gpu: Optional[int]
    shm: Optional[bool]
    gpu_model: Optional[str]

    @classmethod
    def create(
        cls, cpu: float, gpu: int, gpu_model: str, memory: str, extshm: bool
    ) -> "Resources":
        return cls(memory, cpu, gpu, extshm, gpu_model)

    def to_api(self) -> Dict[str, Any]:
        value = {"memory_mb": self.memory_mb, "cpu": self.cpu, "shm": self.shm}
        if self.gpu:
            value["gpu"] = self.gpu
            value["gpu_model"] = self.gpu_model
        return value

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Resources":
        return Resources(
            memory_mb=data["memory_mb"],
            cpu=data["cpu"],
            shm=data.get("shm", None),
            gpu=data.get("gpu", None),
            gpu_model=data.get("gpu_model", None),
        )


@dataclass(frozen=True)
class NetworkPortForwarding:
    ports: Mapping[str, int]
    http_auth: bool = True

    @classmethod
    def from_cli(
        cls, http: SupportsInt, http_auth: bool = False
    ) -> Optional["NetworkPortForwarding"]:
        net = None
        ports: Dict[str, int] = {}
        if http:
            ports["http"] = int(http)
        if ports:
            net = NetworkPortForwarding(ports=ports, http_auth=http_auth)
        return net


@dataclass(frozen=True)
class Image:
    image: str
    command: Optional[str]


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
class Volume:
    storage_path: str
    container_path: str
    read_only: bool

    def to_api(self) -> Dict[str, Any]:
        resp: Dict[str, Any] = {
            "src_storage_uri": self.storage_path,
            "dst_path": self.container_path,
            "read_only": bool(self.read_only),
        }
        return resp

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Volume":
        storage_path = data["src_storage_uri"]
        container_path = data["dst_path"]
        read_only = data.get("read_only", True)
        return Volume(
            storage_path=storage_path,
            container_path=container_path,
            read_only=read_only,
        )

    @classmethod
    def from_cli(cls, username: str, volume: str) -> "Volume":
        parts = volume.split(":")

        read_only = False
        if len(parts) == 4:
            if parts[-1] not in ["ro", "rw"]:
                raise ValueError(f"Wrong ReadWrite/ReadOnly mode spec for '{volume}'")
            read_only = parts.pop() == "ro"
        elif len(parts) != 3:
            raise ValueError(f"Invalid volume specification '{volume}'")

        container_path = parts.pop()
        storage_path = normalize_storage_path_uri(URL(":".join(parts)), username)

        return Volume(
            storage_path=str(storage_path),
            container_path=container_path,
            read_only=read_only,
        )

    @classmethod
    def from_cli_list(
        cls, username: str, lst: Sequence[str]
    ) -> Optional[List["Volume"]]:
        if not lst:
            return None
        return [cls.from_cli(username, s) for s in lst]


@dataclass(frozen=True)
class HTTPPort:
    port: int
    health_check_path: Optional[str] = None
    requires_auth: bool = False

    def to_api(self) -> Dict[str, Any]:
        ret: Dict[str, Any] = {"port": self.port, "requires_auth": self.requires_auth}
        if self.health_check_path is not None:
            ret["health_check_path"] = self.health_check_path
        return ret

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "HTTPPort":
        return HTTPPort(
            port=data.get("port", -1),
            health_check_path=data.get("health_check_path"),
            requires_auth=data.get("requires_auth", False),
        )


def network_to_api(
    network: Optional["NetworkPortForwarding"]
) -> Optional[HTTPPort]:
    http = None
    if network and "http" in network.ports:
        http = HTTPPort.from_api(
            {"port": network.ports["http"], "requires_auth": network.http_auth}
        )
    return http


@dataclass(frozen=True)
class Container:
    image: str
    resources: Resources
    command: Optional[str] = None
    http: Optional[HTTPPort] = None
    # TODO (ASvetlov): replace mutable Dict and List with immutable Mapping and Sequence
    env: Dict[str, str] = field(default_factory=dict)
    volumes: Sequence[Volume] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Container":
        return Container(
            image=data["image"],
            resources=Resources.from_api(data["resources"]),
            command=data.get("command", None),
            http=HTTPPort.from_api(data["http"]) if "http" in data else None,
            env=data.get("env", dict()),
            volumes=[Volume.from_api(v) for v in data.get("volumes", [])],
        )

    def to_api(self) -> Dict[str, Any]:
        primitive: Dict[str, Any] = {
            "image": self.image,
            "resources": self.resources.to_api(),
        }
        if self.command:
            primitive["command"] = self.command
        if self.http:
            primitive["http"] = self.http.to_api()
        if self.env:
            primitive["env"] = self.env
        if self.volumes:
            primitive["volumes"] = [v.to_api() for v in self.volumes]
        return primitive


@dataclass(frozen=True)
class ContainerPayload:
    image: str
    command: Optional[str]
    http: Optional[Mapping[str, int]]
    resources: Resources
    env: Optional[Mapping[str, str]] = None

    def to_primitive(self) -> Dict[str, Any]:
        primitive = {"image": self.image, "resources": self.resources.to_api()}
        if self.command:
            primitive["command"] = self.command
        if self.http:
            primitive["http"] = self.http
        if self.env:
            primitive["env"] = self.env
        return primitive


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
    id: str
    owner: str
    status: JobStatus
    history: JobStatusHistory
    container: Container
    is_preemptible: bool
    ssh_auth_server: URL
    name: Optional[str] = None
    description: Optional[str] = None
    http_url: URL = URL()
    ssh_server: URL = URL()
    internal_hostname: Optional[str] = None

    def jump_host(self) -> Optional[str]:
        ssh_hostname = self.ssh_server.host
        if ssh_hostname is None:
            return None
        ssh_hostname = ".".join(ssh_hostname.split(".")[1:])
        return ssh_hostname

    @classmethod
    def from_api(cls, res: Dict[str, Any]) -> "JobDescription":
        container = Container.from_api(res["container"])
        owner = res["owner"]
        name = res.get("name")
        description = res.get("description")
        history = JobStatusHistory(
            status=JobStatus(res["history"].get("status", "unknown")),
            reason=res["history"].get("reason", ""),
            description=res["history"].get("description", ""),
            created_at=res["history"].get("created_at", ""),
            started_at=res["history"].get("started_at", ""),
            finished_at=res["history"].get("finished_at", ""),
        )
        http_url = URL(res["http_url"]) if "http_url" in res else URL()
        ssh_server = URL(res["ssh_server"]) if "ssh_server" in res else URL()
        internal_hostname = res.get("internal_hostname", None)
        return JobDescription(
            status=JobStatus(res["status"]),
            id=res["id"],
            owner=owner,
            history=history,
            container=container,
            is_preemptible=res["is_preemptible"],
            name=name,
            description=description,
            http_url=http_url,
            ssh_server=ssh_server,
            ssh_auth_server=URL(res["ssh_auth_server"]),
            internal_hostname=internal_hostname,
        )


@dataclass(frozen=True)
class JobTelemetry:
    cpu: float
    memory: float
    timestamp: float
    gpu_duty_cycle: Optional[int] = None
    gpu_memory: Optional[float] = None

    @classmethod
    def from_api(cls, value: Dict[str, Any]) -> "JobTelemetry":
        return cls(
            cpu=value["cpu"],
            memory=value["memory"],
            timestamp=value["timestamp"],
            gpu_duty_cycle=value.get("gpu_duty_cycle"),
            gpu_memory=value.get("gpu_memory"),
        )


class Jobs:
    def __init__(self, core: Core, token: str) -> None:
        self._core = core
        self._token = token

    async def submit(
        self,
        *,
        image: Image,
        resources: Resources,
        network: Optional[NetworkPortForwarding],
        volumes: Optional[List[Volume]],
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_preemptible: bool = False,
        env: Optional[Dict[str, str]] = None,
    ) -> JobDescription:
        http = network_to_api(network)
        if env is None:
            real_env: Dict[str, str] = {}
        else:
            real_env = env
        if volumes is not None:
            volumes = volumes
        else:
            volumes = []
        container = Container(
            image=image.image,
            command=image.command,
            http=http,
            resources=resources,
            env=real_env,
            volumes=volumes,
        )

        url = URL("jobs")
        payload: Dict[str, Any] = {
            "container": container.to_api(),
            "is_preemptible": is_preemptible,
        }
        if name:
            payload["name"] = name
        if description:
            payload["description"] = description
        async with self._core.request("POST", url, json=payload) as resp:
            res = await resp.json()
            return JobDescription.from_api(res)

    async def list(
        self, statuses: Optional[Set[str]] = None, name: Optional[str] = None
    ) -> List[JobDescription]:
        url = URL(f"jobs")
        params: MultiDict[str] = MultiDict()
        if statuses:
            for status in statuses:
                params.add("status", status)
        if name:
            params.add("name", name)
        async with self._core.request("GET", url, params=params) as resp:
            ret = await resp.json()
            return [JobDescription.from_api(j) for j in ret["jobs"]]

    async def kill(self, id: str) -> None:
        url = URL(f"jobs/{id}")
        async with self._core.request("DELETE", url):
            # an error is raised for status >= 400
            return None  # 201 status code

    async def monitor(
        self, id: str
    ) -> Any:  # real type is async generator with data chunks
        url = URL(f"jobs/{id}/log")
        async with self._core.request(
            "GET", url, headers={"Accept-Encoding": "identity"}
        ) as resp:
            async for data in resp.content.iter_any():
                yield data

    async def status(self, id: str) -> JobDescription:
        url = URL(f"jobs/{id}")
        async with self._core.request("GET", url) as resp:
            ret = await resp.json()
            return JobDescription.from_api(ret)

    async def top(self, id: str) -> AsyncIterator[JobTelemetry]:
        url = URL(f"jobs/{id}/top")
        try:
            received_any = False
            async for resp in self._core.ws_connect(url):
                yield JobTelemetry.from_api(resp.json())  # type: ignore
                received_any = True
            if not received_any:
                raise ValueError(f"Job is not running. Job Id = {id}")
        except WSServerHandshakeError as e:
            if e.status == 400:
                raise ValueError(f"Job not found. Job Id = {id}")
            raise

    async def exec(self, id: str, tty: bool, no_key_check: bool, cmd: List[str]) -> int:
        try:
            job_status = await self.status(id)
        except IllegalArgumentError as e:
            raise ValueError(f"Job not found. Job Id = {id}") from e
        if job_status.status != "running":
            raise ValueError(f"Job is not running. Job Id = {id}")
        payload = json.dumps(
            {
                "method": "job_exec",
                "token": self._token,
                "params": {"job": id, "command": cmd},
            }
        )
        command = ["ssh"]
        if tty:
            command += ["-tt"]
        else:
            command += ["-T"]
        if no_key_check:  # pragma: no branch
            command += [
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
            ]
        server_url = job_status.ssh_auth_server
        port = server_url.port if server_url.port else 22
        command += ["-p", str(port), f"{server_url.user}@{server_url.host}", payload]
        proc = await asyncio.create_subprocess_exec(*command)
        try:
            return await proc.wait()
        finally:
            await kill_proc_tree(proc.pid, timeout=10)
            # add a sleep to get process watcher a chance to execute all callbacks
            await asyncio.sleep(0.1)

    async def port_forward(
        self, id: str, no_key_check: bool, local_port: int, job_port: int
    ) -> int:
        try:
            job_status = await self.status(id)
        except IllegalArgumentError as e:
            raise ValueError(f"Job not found. Job Id = {id}") from e
        if job_status.status != "running":
            raise ValueError(f"Job is not running. Job Id = {id}")
        payload = json.dumps(
            {
                "method": "job_port_forward",
                "token": self._token,
                "params": {"job": id, "port": job_port},
            }
        )
        proxy_command = ["ssh"]
        if no_key_check:  # pragma: no branch
            proxy_command += [
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
            ]
        server_url = job_status.ssh_auth_server
        port = server_url.port if server_url.port else 22
        proxy_command += [
            "-p",
            str(port),
            f"{server_url.user}@{server_url.host}",
            payload,
        ]
        proxy_command_str = " ".join(shlex.quote(s) for s in proxy_command)
        command = [
            "ssh",
            "-NL",
            f"{local_port}:{id}:{job_port}",
            "-o",
            f"ProxyCommand={proxy_command_str}",
            "-o",
            "ExitOnForwardFailure=yes",
        ]
        if no_key_check:  # pragma: no branch
            command += [
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
            ]
        command += [f"{server_url.user}@{server_url.host}"]
        print(f"Port of {id} is forwarded to localhost:{local_port}")
        print(f"Press ^C to stop forwarding")
        proc = await asyncio.create_subprocess_exec(*command)
        try:
            return await proc.wait()
        finally:
            await kill_proc_tree(proc.pid, timeout=10)
            # add a sleep to get process watcher a chance to execute all callbacks
            await asyncio.sleep(0.1)
