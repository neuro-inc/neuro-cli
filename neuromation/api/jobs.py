import asyncio
import enum
import json
import shlex
import signal
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, Iterable, List, Mapping, Optional, Sequence

import attr
import psutil
from aiodocker.exceptions import DockerError
from aiohttp import WSServerHandshakeError
from dateutil.parser import isoparse
from multidict import MultiDict
from yarl import URL

from neuromation.api.abc import (
    AbstractDockerImageProgress,
    ImageCommitFinished,
    ImageCommitStarted,
    ImageProgressPush,
    ImageProgressSave,
)

from .config import Config
from .core import IllegalArgumentError, _Core
from .images import (
    _DummyProgress,
    _raise_on_error_chunk,
    _try_parse_image_progress_step,
)
from .parser import Parser, Volume
from .parsing_utils import LocalImage, RemoteImage, _as_repo_str, _is_in_neuro_registry
from .utils import NoPublicConstructor, asynccontextmanager


INVALID_IMAGE_NAME = "INVALID-IMAGE-NAME"


@dataclass(frozen=True)
class Resources:
    memory_mb: int
    cpu: float
    gpu: Optional[int] = None
    gpu_model: Optional[str] = None
    shm: bool = True
    tpu_type: Optional[str] = None
    tpu_software_version: Optional[str] = None


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
class HTTPPort:
    port: int
    requires_auth: bool = True


@dataclass(frozen=True)
class Container:
    image: RemoteImage
    resources: Resources
    entrypoint: Optional[str] = None
    command: Optional[str] = None
    http: Optional[HTTPPort] = None
    env: Mapping[str, str] = field(default_factory=dict)
    volumes: Sequence[Volume] = field(default_factory=list)
    tty: bool = False


@dataclass(frozen=True)
class JobStatusHistory:
    status: JobStatus
    reason: str
    description: str
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    exit_code: Optional[int] = None


class JobRestartPolicy(str, enum.Enum):
    NEVER = "never"
    ON_FAILURE = "on-failure"
    ALWAYS = "always"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return repr(self.value)


@dataclass(frozen=True)
class JobDescription:
    id: str
    owner: str
    cluster_name: str
    status: JobStatus
    history: JobStatusHistory
    container: Container
    is_preemptible: bool
    uri: URL
    name: Optional[str] = None
    tags: Sequence[str] = ()
    description: Optional[str] = None
    http_url: URL = URL()
    ssh_server: URL = URL()
    internal_hostname: Optional[str] = None
    restart_policy: JobRestartPolicy = JobRestartPolicy.NEVER
    life_span: Optional[float] = None


@dataclass(frozen=True)
class JobTelemetry:
    cpu: float
    memory: float
    timestamp: float
    gpu_duty_cycle: Optional[int] = None
    gpu_memory: Optional[float] = None


class Jobs(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: Config, parse: Parser) -> None:
        self._core = core
        self._config = config
        self._parse = parse

    async def run(
        self,
        container: Container,
        *,
        name: Optional[str] = None,
        tags: Sequence[str] = (),
        description: Optional[str] = None,
        is_preemptible: bool = False,
        schedule_timeout: Optional[float] = None,
        restart_policy: JobRestartPolicy = JobRestartPolicy.NEVER,
        life_span: Optional[float] = None,
    ) -> JobDescription:
        url = self._config.api_url / "jobs"
        payload: Dict[str, Any] = {
            "container": _container_to_api(container),
            "is_preemptible": is_preemptible,
        }
        if name:
            payload["name"] = name
        if tags:
            payload["tags"] = tags
        if description:
            payload["description"] = description
        if schedule_timeout:
            payload["schedule_timeout"] = schedule_timeout
        if restart_policy != JobRestartPolicy.NEVER:
            payload["restart_policy"] = str(restart_policy)
        if life_span is not None:
            payload["max_run_time_minutes"] = int(life_span // 60)
        payload["cluster_name"] = self._config.cluster_name
        auth = await self._config._api_auth()
        async with self._core.request("POST", url, json=payload, auth=auth) as resp:
            res = await resp.json()
            return _job_description_from_api(res, self._parse)

    async def list(
        self,
        *,
        statuses: Iterable[JobStatus] = (),
        name: str = "",
        tags: Iterable[str] = (),
        owners: Iterable[str] = (),
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        reverse: bool = False,
        limit: Optional[int] = None,
    ) -> AsyncIterator[JobDescription]:
        url = self._config.api_url / "jobs"
        headers = {"Accept": "application/x-ndjson"}
        params: MultiDict[str] = MultiDict()
        for status in statuses:
            params.add("status", status.value)
        if name:
            params.add("name", name)
        for owner in owners:
            params.add("owner", owner)
        for tag in tags:
            params.add("tag", tag)
        if since:
            if since.tzinfo is None:
                # Interpret naive datetime object as local time.
                since = since.astimezone(timezone.utc)
            params.add("since", since.isoformat())
        if until:
            if until.tzinfo is None:
                until = until.astimezone(timezone.utc)
            params.add("until", until.isoformat())
        params["cluster_name"] = self._config.cluster_name
        if reverse:
            params.add("reverse", "1")
        if limit is not None:
            params.add("limit", str(limit))
        auth = await self._config._api_auth()
        async with self._core.request(
            "GET", url, headers=headers, params=params, auth=auth
        ) as resp:
            if resp.headers.get("Content-Type", "").startswith("application/x-ndjson"):
                async for line in resp.content:
                    j = json.loads(line)
                    yield _job_description_from_api(j, self._parse)
            else:
                ret = await resp.json()
                for j in ret["jobs"]:
                    yield _job_description_from_api(j, self._parse)

    async def kill(self, id: str) -> None:
        url = self._config.api_url / "jobs" / id
        auth = await self._config._api_auth()
        async with self._core.request("DELETE", url, auth=auth):
            # an error is raised for status >= 400
            return None  # 201 status code

    async def monitor(self, id: str) -> AsyncIterator[bytes]:
        url = self._config.monitoring_url / id / "log"
        timeout = attr.evolve(self._core.timeout, sock_read=None)
        auth = await self._config._api_auth()
        async with self._core.request(
            "GET",
            url,
            headers={"Accept-Encoding": "identity"},
            timeout=timeout,
            auth=auth,
        ) as resp:
            async for data in resp.content.iter_any():
                yield data

    async def status(self, id: str) -> JobDescription:
        url = self._config.api_url / "jobs" / id
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            ret = await resp.json()
            return _job_description_from_api(ret, self._parse)

    async def tags(self) -> List[str]:
        url = self._config.api_url / "tags"
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            ret = await resp.json()
            return ret["tags"]

    async def top(self, id: str) -> AsyncIterator[JobTelemetry]:
        url = self._config.monitoring_url / id / "top"
        auth = await self._config._api_auth()
        try:
            received_any = False
            async for resp in self._core.ws_connect(url, auth=auth):
                yield _job_telemetry_from_api(resp.json())
                received_any = True
            if not received_any:
                raise ValueError(f"Job is not running. Job Id = {id}")
        except WSServerHandshakeError as e:
            if e.status == 400:
                raise ValueError(f"Job not found. Job Id = {id}")
            raise

    async def save(
        self,
        id: str,
        image: RemoteImage,
        *,
        progress: Optional[AbstractDockerImageProgress] = None,
    ) -> None:
        if not _is_in_neuro_registry(image):
            raise ValueError(f"Image `{image}` must be in the neuromation registry")
        if progress is None:
            progress = _DummyProgress()

        payload = {"container": {"image": _as_repo_str(image)}}
        url = self._config.monitoring_url / id / "save"

        auth = await self._config._api_auth()
        timeout = attr.evolve(self._core.timeout, sock_read=None)
        # `self._code.request` implicitly sets `total=3 * 60`
        # unless `sock_read is None`
        async with self._core.request(
            "POST", url, json=payload, timeout=timeout, auth=auth
        ) as resp:
            # first, we expect exactly two docker-commit messages
            progress.save(ImageProgressSave(id, image))

            chunk_1 = await resp.content.readline()
            data_1 = _parse_commit_started_chunk(id, _load_chunk(chunk_1), self._parse)
            progress.commit_started(data_1)

            chunk_2 = await resp.content.readline()
            data_2 = _parse_commit_finished_chunk(id, _load_chunk(chunk_2))
            progress.commit_finished(data_2)

            # then, we expect stream for docker-push
            src = LocalImage(f"{image.owner}/{image.name}", image.tag)
            progress.push(ImageProgressPush(src, dst=image))
            async for chunk in resp.content:
                obj = _load_chunk(chunk)
                push_step = _try_parse_image_progress_step(obj, image.tag)
                if push_step:
                    progress.step(push_step)

    async def exec(
        self,
        id: str,
        cmd: Iterable[str],
        *,
        tty: bool = False,
        no_key_check: bool = False,
    ) -> int:
        try:
            job_status = await self.status(id)
        except IllegalArgumentError as e:
            raise ValueError(f"Job not found. Job Id = {id}") from e
        if job_status.status != "running":
            raise ValueError(f"Job is not running. Job Id = {job_status.id}")
        payload = json.dumps(
            {
                "method": "job_exec",
                "token": await self._config.token(),
                "params": {"job": job_status.id, "command": list(cmd)},
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
        server_url = job_status.ssh_server
        port = server_url.port if server_url.port else 22
        command += ["-p", str(port), f"{server_url.user}@{server_url.host}", payload]
        proc = await asyncio.create_subprocess_exec(*command)
        try:
            return await proc.wait()
        finally:
            await _kill_proc_tree(proc.pid, timeout=10)
            # add a sleep to get process watcher a chance to execute all callbacks
            await asyncio.sleep(0.1)

    @asynccontextmanager
    async def port_forward(
        self, id: str, local_port: int, job_port: int, *, no_key_check: bool = False
    ) -> AsyncIterator[None]:
        loop = asyncio.get_event_loop()
        task = loop.create_task(
            self._port_forward(id, local_port, job_port, no_key_check=no_key_check)
        )
        yield
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    async def _port_forward(
        self, id: str, local_port: int, job_port: int, *, no_key_check: bool = False
    ) -> None:
        try:
            job_status = await self.status(id)
        except IllegalArgumentError as e:
            raise ValueError(f"Job not found. Job Id = {id}") from e
        if job_status.status != "running":
            raise ValueError(f"Job is not running. Job Id = {job_status.id}")
        payload = json.dumps(
            {
                "method": "job_port_forward",
                "token": await self._config.token(),
                "params": {"job": job_status.id, "port": job_port},
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
        server_url = job_status.ssh_server
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
            f"{local_port}:{job_status.internal_hostname}:{job_port}",
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
        proc = await asyncio.create_subprocess_exec(*command)
        try:
            result = await proc.wait()
            if result != 0:
                raise ValueError(f"error code {result}")
            return
        finally:
            await _kill_proc_tree(proc.pid, timeout=10)
            # add a sleep to get process watcher a chance to execute all callbacks
            await asyncio.sleep(0.1)


#  ############## Internal helpers ###################


def _load_chunk(chunk: bytes) -> Dict[str, Any]:
    return json.loads(chunk, encoding="utf-8")


def _parse_commit_started_chunk(
    job_id: str, obj: Dict[str, Any], parse: Parser
) -> ImageCommitStarted:
    _raise_for_invalid_commit_chunk(obj, expect_started=True)
    details_json = obj.get("details", {})
    image = details_json.get("image")
    if not image:
        error_details = {"message": "Missing required details: 'image'"}
        raise DockerError(400, error_details)
    return ImageCommitStarted(job_id, parse.remote_image(image))


def _parse_commit_finished_chunk(
    job_id: str, obj: Dict[str, Any]
) -> ImageCommitFinished:
    _raise_for_invalid_commit_chunk(obj, expect_started=False)
    return ImageCommitFinished(job_id)


def _raise_for_invalid_commit_chunk(obj: Dict[str, Any], expect_started: bool) -> None:
    _raise_on_error_chunk(obj)
    if "status" not in obj.keys():
        error_details = {"message": 'Missing required field: "status"'}
        raise DockerError(400, error_details)
    status = obj["status"]
    expected = "CommitStarted" if expect_started else "CommitFinished"
    if status != expected:
        error_details = {
            "message": f"Invalid commit status: '{status}', expecting: '{expected}'"
        }
        raise DockerError(400, error_details)


def _resources_to_api(resources: Resources) -> Dict[str, Any]:
    value: Dict[str, Any] = {
        "memory_mb": resources.memory_mb,
        "cpu": resources.cpu,
        "shm": resources.shm,
    }
    if resources.gpu:
        value["gpu"] = resources.gpu
        value["gpu_model"] = resources.gpu_model
    if resources.tpu_type:
        assert resources.tpu_software_version
        value["tpu"] = {
            "type": resources.tpu_type,
            "software_version": resources.tpu_software_version,
        }
    return value


def _resources_from_api(data: Dict[str, Any]) -> Resources:
    tpu_type = tpu_software_version = None
    if "tpu" in data:
        tpu = data["tpu"]
        tpu_type = tpu["type"]
        tpu_software_version = tpu["software_version"]
    return Resources(
        memory_mb=data["memory_mb"],
        cpu=data["cpu"],
        shm=data.get("shm", True),
        gpu=data.get("gpu", None),
        gpu_model=data.get("gpu_model", None),
        tpu_type=tpu_type,
        tpu_software_version=tpu_software_version,
    )


def _http_port_to_api(port: HTTPPort) -> Dict[str, Any]:
    return {"port": port.port, "requires_auth": port.requires_auth}


def _http_port_from_api(data: Dict[str, Any]) -> HTTPPort:
    return HTTPPort(
        port=data.get("port", -1), requires_auth=data.get("requires_auth", False)
    )


def _container_from_api(data: Dict[str, Any], parse: Parser) -> Container:
    try:
        image = parse.remote_image(data["image"])
    except ValueError:
        image = RemoteImage.new_external_image(name=INVALID_IMAGE_NAME)

    return Container(
        image=image,
        resources=_resources_from_api(data["resources"]),
        entrypoint=data.get("entrypoint", None),
        command=data.get("command", None),
        http=_http_port_from_api(data["http"]) if "http" in data else None,
        env=data.get("env", dict()),
        volumes=[_volume_from_api(v) for v in data.get("volumes", [])],
        tty=data.get("tty", False),
    )


def _container_to_api(container: Container) -> Dict[str, Any]:
    primitive: Dict[str, Any] = {
        "image": _as_repo_str(container.image),
        "resources": _resources_to_api(container.resources),
    }
    if container.entrypoint:
        primitive["entrypoint"] = container.entrypoint
    if container.command:
        primitive["command"] = container.command
    if container.http:
        primitive["http"] = _http_port_to_api(container.http)
    if container.env:
        primitive["env"] = container.env
    if container.volumes:
        primitive["volumes"] = [_volume_to_api(v) for v in container.volumes]
    if container.tty:
        primitive["tty"] = True
    return primitive


def _job_description_from_api(res: Dict[str, Any], parse: Parser) -> JobDescription:
    container = _container_from_api(res["container"], parse)
    owner = res["owner"]
    cluster_name = res["cluster_name"]
    name = res.get("name")
    tags = res.get("tags", ())
    description = res.get("description")
    history = JobStatusHistory(
        status=JobStatus(res["history"].get("status", "unknown")),
        reason=res["history"].get("reason", ""),
        description=res["history"].get("description", ""),
        created_at=_parse_datetime(res["history"].get("created_at")),
        started_at=_parse_datetime(res["history"].get("started_at")),
        finished_at=_parse_datetime(res["history"].get("finished_at")),
        exit_code=res["history"].get("exit_code"),
    )
    http_url = URL(res.get("http_url", ""))
    http_url_named = URL(res.get("http_url_named", ""))
    ssh_server = URL(res.get("ssh_server", ""))
    internal_hostname = res.get("internal_hostname", None)
    restart_policy = JobRestartPolicy(res.get("restart_policy", JobRestartPolicy.NEVER))
    max_run_time_minutes = res.get("max_run_time_minutes")
    life_span = (
        max_run_time_minutes * 60.0 if max_run_time_minutes is not None else None
    )
    return JobDescription(
        status=JobStatus(res["status"]),
        id=res["id"],
        owner=owner,
        cluster_name=cluster_name,
        history=history,
        container=container,
        is_preemptible=res["is_preemptible"],
        name=name,
        tags=tags,
        description=description,
        http_url=http_url_named or http_url,
        ssh_server=ssh_server,
        internal_hostname=internal_hostname,
        uri=URL(res["uri"]),
        restart_policy=restart_policy,
        life_span=life_span,
    )


def _job_telemetry_from_api(value: Dict[str, Any]) -> JobTelemetry:
    return JobTelemetry(
        cpu=value["cpu"],
        memory=value["memory"],
        timestamp=value["timestamp"],
        gpu_duty_cycle=value.get("gpu_duty_cycle"),
        gpu_memory=value.get("gpu_memory"),
    )


def _volume_to_api(volume: Volume) -> Dict[str, Any]:
    resp: Dict[str, Any] = {
        "src_storage_uri": str(volume.storage_uri),
        "dst_path": volume.container_path,
        "read_only": bool(volume.read_only),
    }
    return resp


def _volume_from_api(data: Dict[str, Any]) -> Volume:
    storage_uri = URL(data["src_storage_uri"])
    container_path = data["dst_path"]
    read_only = data.get("read_only", True)
    return Volume(
        storage_uri=storage_uri, container_path=container_path, read_only=read_only
    )


def _parse_datetime(dt: Optional[str]) -> Optional[datetime]:
    if dt is None:
        return None
    return isoparse(dt)


async def _kill_proc_tree(
    pid: int,
    sig: int = signal.SIGTERM,
    include_parent: bool = True,
    timeout: int = None,
) -> None:
    """Kill a process tree (including grandchildren) with signal
    "sig".
    """

    def inner() -> None:
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            zombies: List[psutil.Process] = []
            # Try to kill all children first
            for p in children:
                try:
                    p.send_signal(sig)
                except psutil.NoSuchProcess:
                    pass
            _, children_alive = psutil.wait_procs(children, timeout=timeout)
            # then kill parent
            if include_parent:
                parent.send_signal(sig)
                try:
                    parent.wait(timeout=timeout)
                    # and try to kill again left childrent
                    _, children_alive = psutil.wait_procs(
                        children_alive, timeout=timeout
                    )
                    zombies.extend(children_alive)
                except psutil.TimeoutExpired:
                    zombies.append(parent)
            else:
                zombies.extend(children_alive)

            if zombies:
                raise RuntimeWarning(f"Possible zombie subprocesses: {zombies}")

        except psutil.NoSuchProcess:
            pass

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, inner)
