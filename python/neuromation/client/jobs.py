import asyncio
import enum
from contextlib import contextmanager
from io import BufferedReader
from typing import Dict, List, Optional

from dataclasses import dataclass

from neuromation.http.fetch import FetchError
from neuromation.strings import parse

from .client import ApiClient
from .requests import (ContainerPayload, InferRequest, JobKillRequest,
                       JobListRequest, JobMonitorRequest, JobStatusRequest,
                       ResourcesPayload, TrainRequest)


@dataclass(frozen=True)
class Resources:
    memory: str
    cpu: float
    gpu: Optional[int]
    shm: Optional[bool]


@dataclass()
class NetworkPortForwarding:
    ports: Dict[str, int]


@dataclass(frozen=True)
class Image:
    image: str
    command: str


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
    url: str = ''
    history: JobStatusHistory = None
    resources: Resources = None


@dataclass(frozen=True)
class JobItem:
    status: str
    id: str
    client: ApiClient
    url: str = ''
    history: JobStatusHistory = None

    async def _call(self):
        return JobItem(
            client=self.client,
            **await self.client._fetch(
                request=JobStatusRequest(
                    id=self.id
                )))

    def wait(self, timeout=None):
        try:
            return self.client.loop.run_until_complete(
                asyncio.wait_for(
                    self._call(),
                    timeout=timeout
                )
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

    PENDING = 'pending'
    RUNNING = 'running'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


class Model(ApiClient):

    def infer(
            self,
            *,
            image: Image,
            resources: Resources,
            network: NetworkPortForwarding,
            model: str,
            dataset: str,
            results: str) -> JobItem:
        res = self._fetch_sync(
            InferRequest(
                container=ContainerPayload(
                    image=image.image,
                    command=image.command,
                    http=None,
                    resources=ResourcesPayload(
                        memory_mb=parse.to_megabytes_str(resources.memory),
                        cpu=resources.cpu,
                        gpu=resources.gpu,
                        shm=resources.shm,
                    )
                ),
                model_storage_uri=model,
                dataset_storage_uri=dataset,
                result_storage_uri=results))

        return JobItem(
            id=res['job_id'],
            status=res['status'],
            client=self)

    def train(
            self,
            *,
            image: Image,
            resources: Resources,
            network: NetworkPortForwarding,
            dataset: str,
            results: str) -> JobItem:
        http = None
        if network:
            if 'http' in network.ports:
                http = {
                    'port': network.ports['http']
                }
        res = self._fetch_sync(
            TrainRequest(
                container=ContainerPayload(
                    image=image.image,
                    command=image.command,
                    http=http,
                    resources=ResourcesPayload(
                        memory_mb=parse.to_megabytes_str(resources.memory),
                        cpu=resources.cpu,
                        gpu=resources.gpu,
                        shm=resources.shm,
                    )
                ),
                dataset_storage_uri=dataset,
                result_storage_uri=results))

        return JobItem(
            id=res['job_id'],
            status=res['status'],
            client=self)


class Job(ApiClient):

    def list(self) -> List[JobDescription]:
        res = self._fetch_sync(JobListRequest())
        return [
            self._dict_to_description(job)
            for job in res['jobs']
        ]

    def kill(self, id: str) -> bool:
        self._fetch_sync(JobKillRequest(id=id))
        # TODO(artyom, 07/16/2018): what are we returning here?
        return True

    @contextmanager
    def monitor(self, id: str) -> BufferedReader:
        try:
            with self._fetch_sync(JobMonitorRequest(id=id)) as content:
                yield BufferedReader(content)
        except FetchError as error:
            error_class = type(error)
            mapped_class = self._exception_map.get(error_class, error_class)
            raise mapped_class(error) from error

    def status(self, id: str) -> JobDescription:
        res = self._fetch_sync(JobStatusRequest(id=id))
        return self._dict_to_description_with_history(res)

    def _dict_to_description_with_history(self, res):
        job_description = self._dict_to_description(res)
        job_history = None
        if 'history' in res:
            job_history = JobStatusHistory(
                status=res['history'].get('status', None),
                reason=res['history'].get('reason', None),
                description=res['history'].get('description', None),
                created_at=res['history'].get('created_at', None),
                started_at=res['history'].get('started_at', None),
                finished_at=res['history'].get('finished_at', None)
            )
        return JobDescription(
            client=self,
            id=job_description.id,
            status=job_description.status,
            image=job_description.image,
            command=job_description.command,
            history=job_history,
            resources=job_description.resources
        )

    def _dict_to_description(self, res):
        job_container_image = None
        job_command = None
        job_resources = None

        if 'container' in res:
            job_container_image = res['container']['image'] \
                if 'image' in res['container'] \
                else None
            job_command = res['container']['command'] \
                if 'command' in res['container'] \
                else None

            if 'resources' in res['container']:
                container_resources = res['container']['resources']
                shm = container_resources.get('shm', None)
                gpu = container_resources.get('gpu', None)
                job_resources = Resources(
                    cpu=container_resources['cpu'],
                    memory=container_resources['memory_mb'],
                    gpu=gpu,
                    shm=shm,
                )
        return JobDescription(
            client=self,
            id=res['id'],
            status=res['status'],
            image=job_container_image,
            command=job_command,
            resources=job_resources
        )
