import abc
import datetime
import itertools
import sys
import time
from dataclasses import dataclass
from typing import Iterable, Iterator, List

import humanize
from click import style, unstyle

from neuromation.api import (
    JobDescription,
    JobRestartPolicy,
    JobStatus,
    JobTelemetry,
    Resources,
)
from neuromation.cli.parse_utils import JobColumnInfo
from neuromation.cli.printer import StreamPrinter, TTYPrinter
from neuromation.cli.utils import format_size

from .ftable import table
from .utils import ImageFormatter, URIFormatter, image_formatter


COLORS = {
    JobStatus.PENDING: "yellow",
    JobStatus.RUNNING: "blue",
    JobStatus.SUCCEEDED: "green",
    JobStatus.FAILED: "red",
    JobStatus.UNKNOWN: "yellow",
}


def format_job_status(status: JobStatus) -> str:
    return style(status.value, fg=COLORS.get(status, "reset"))


def format_timedelta(delta: datetime.timedelta) -> str:
    s = int(delta.total_seconds())
    if s < 0:
        raise ValueError(f"Invalid delta {delta}: expect non-negative total value")
    _sec_in_minute = 60
    _sec_in_hour = _sec_in_minute * 60
    _sec_in_day = _sec_in_hour * 24
    d, s = divmod(s, _sec_in_day)
    h, s = divmod(s, _sec_in_hour)
    m, s = divmod(s, _sec_in_minute)
    return "".join(
        [
            f"{d}d" if d else "",
            f"{h}h" if h else "",
            f"{m}m" if m else "",
            f"{s}s" if s else "",
        ]
    )


class JobFormatter:
    def __init__(self, quiet: bool = True) -> None:
        self._quiet = quiet

    def __call__(self, job: JobDescription) -> str:
        job_id = job.id
        if self._quiet:
            return job_id
        out = []
        out.append(
            style("Job ID", bold=True)
            + f": {job_id} "
            + style("Status", bold=True)
            + f": {format_job_status(job.status)}"
        )
        if job.name:
            out.append(style("Name", bold=True) + f": {job.name}")
            job_alias = job.name
        else:
            job_alias = job.id
        http_url = job.http_url
        if http_url:
            out.append(style("Http URL", bold=True) + f": {http_url}")
        out.append(style("Shortcuts", bold=True) + ":")

        out.append(
            f"  neuro status {job_alias}     " + style("# check job status", dim=True)
        )
        out.append(
            f"  neuro logs {job_alias}       " + style("# monitor job stdout", dim=True)
        )
        out.append(
            f"  neuro top {job_alias}        "
            + style("# display real-time job telemetry", dim=True)
        )
        out.append(
            f"  neuro exec {job_alias} bash  "
            + style("# execute bash shell to the job", dim=True)
        )
        out.append(f"  neuro kill {job_alias}       " + style("# kill job", dim=True))
        return "\n".join(out)


class JobStatusFormatter:
    def __init__(self, uri_formatter: URIFormatter) -> None:
        self._format_uri = uri_formatter
        self._format_image = image_formatter(uri_formatter=uri_formatter)

    def __call__(self, job_status: JobDescription) -> str:
        result: str = f"Job: {job_status.id}\n"
        if job_status.name:
            result += f"Name: {job_status.name}\n"
        if job_status.tags:
            result += f"Tags: {', '.join(job_status.tags)}\n"
        result += f"Owner: {job_status.owner if job_status.owner else ''}\n"
        result += f"Cluster: {job_status.cluster_name}\n"
        if job_status.description:
            result += f"Description: {job_status.description}\n"
        result += f"Status: {job_status.status}"
        if (
            job_status.history
            and job_status.history.reason
            and job_status.status in [JobStatus.FAILED, JobStatus.PENDING]
        ):
            result += f" ({job_status.history.reason})"
        result += f"\nImage: {self._format_image(job_status.container.image)}\n"

        if job_status.container.entrypoint:
            result += f"Entrypoint: {job_status.container.entrypoint}\n"
        result += f"Command: {job_status.container.command}\n"
        resource_formatter = ResourcesFormatter()
        result += resource_formatter(job_status.container.resources) + "\n"
        result += f"Preemptible: {job_status.is_preemptible}\n"
        if job_status.restart_policy != JobRestartPolicy.NEVER:
            result += f"Restart policy: {job_status.restart_policy}\n"
        if job_status.life_span is not None:
            limit = (
                "no limit"
                if job_status.life_span == 0
                else format_timedelta(datetime.timedelta(seconds=job_status.life_span))
            )
            result += f"Life span: {limit}\n"

        if job_status.container.tty:
            result += "TTY: True\n"

        if job_status.container.volumes:
            rows = [
                (
                    volume.container_path,
                    f"{self._format_uri(volume.storage_uri)}",
                    "READONLY" if volume.read_only else " ",
                )
                for volume in job_status.container.volumes
            ]
            result += "Volumes:" + "\n  "
            result += "\n  ".join(table(rows)) + "\n"

        if job_status.internal_hostname:
            result += f"Internal Hostname: {job_status.internal_hostname}\n"
        if job_status.http_url:
            result = f"{result}Http URL: {job_status.http_url}\n"
        if job_status.container.http:
            result = (
                f"{result}Http authentication: "
                f"{job_status.container.http.requires_auth}\n"
            )
        if job_status.container.env:
            result += f"Environment:\n"
            for key, value in job_status.container.env.items():
                result += f"{key}={value}\n"

        assert job_status.history is not None
        assert job_status.history.created_at is not None
        created_at = job_status.history.created_at.isoformat()
        result = f"{result}Created: {created_at}"
        if job_status.status in [
            JobStatus.RUNNING,
            JobStatus.FAILED,
            JobStatus.SUCCEEDED,
        ]:
            assert job_status.history.started_at is not None
            started_at = job_status.history.started_at.isoformat()
            result += "\n" f"Started: {started_at}"
        if job_status.status in [JobStatus.FAILED, JobStatus.SUCCEEDED]:
            assert job_status.history.finished_at is not None
            finished_at = job_status.history.finished_at.isoformat()
            result += "\n" f"Finished: {finished_at}"
            result += "\n" f"Exit code: {job_status.history.exit_code}"
        if job_status.status == JobStatus.FAILED:
            result += "\n===Description===\n"
            result += f"{job_status.history.description}\n================="
        return result


class JobTelemetryFormatter:
    def __init__(self) -> None:
        self.col_len = {
            "timestamp": 24,
            "cpu": 15,
            "memory": 15,
            "gpu": 15,
            "gpu_memory": 15,
        }

    def _format_timestamp(self, timestamp: float) -> str:
        # NOTE: ctime returns time wrt timezone
        return str(time.ctime(timestamp))

    def header(self) -> str:
        return "\t".join(
            [
                "TIMESTAMP".ljust(self.col_len["timestamp"]),
                "CPU".ljust(self.col_len["cpu"]),
                "MEMORY (MB)".ljust(self.col_len["memory"]),
                "GPU (%)".ljust(self.col_len["gpu"]),
                "GPU_MEMORY (MB)".ljust(self.col_len["gpu_memory"]),
            ]
        )

    def __call__(self, info: JobTelemetry) -> str:
        timestamp = self._format_timestamp(info.timestamp)
        cpu = f"{info.cpu:.3f}"
        mem = f"{info.memory:.3f}"
        gpu = f"{info.gpu_duty_cycle}" if info.gpu_duty_cycle else "0"
        gpu_mem = f"{info.gpu_memory:.3f}" if info.gpu_memory else "0"
        return "\t".join(
            [
                timestamp.ljust(self.col_len["timestamp"]),
                cpu.ljust(self.col_len["cpu"]),
                mem.ljust(self.col_len["memory"]),
                gpu.ljust(self.col_len["gpu"]),
                gpu_mem.ljust(self.col_len["gpu_memory"]),
            ]
        )


class BaseJobsFormatter:
    @abc.abstractmethod
    def __call__(
        self, jobs: Iterable[JobDescription]
    ) -> Iterator[str]:  # pragma: no cover
        pass


class SimpleJobsFormatter(BaseJobsFormatter):
    def __call__(self, jobs: Iterable[JobDescription]) -> Iterator[str]:
        for job in jobs:
            yield job.id


@dataclass(frozen=True)
class TabularJobRow:
    id: str
    name: str
    tags: str
    status: str
    when: str
    image: str
    owner: str
    description: str
    cluster_name: str
    command: str

    @classmethod
    def from_job(
        cls, job: JobDescription, username: str, image_formatter: ImageFormatter
    ) -> "TabularJobRow":
        if job.status == JobStatus.PENDING:
            when = job.history.created_at
        elif job.status == JobStatus.RUNNING:
            when = job.history.started_at
        else:
            when = job.history.finished_at
        assert when is not None
        assert when.tzinfo is not None
        delta = datetime.datetime.now(datetime.timezone.utc) - when
        if delta < datetime.timedelta(days=1):
            when_humanized = humanize.naturaltime(delta)
        else:
            when_humanized = humanize.naturaldate(when.astimezone())
        return cls(
            id=job.id,
            name=job.name if job.name else "",
            tags=",".join(job.tags),
            status=job.status,
            when=when_humanized,
            image=image_formatter(job.container.image),
            owner=("<you>" if job.owner == username else job.owner),
            description=job.description if job.description else "",
            cluster_name=job.cluster_name,
            command=job.container.command if job.container.command else "",
        )

    def to_list(self, columns: List[JobColumnInfo]) -> List[str]:
        return [getattr(self, column.id) for column in columns]


class TabularJobsFormatter(BaseJobsFormatter):
    def __init__(
        self,
        width: int,
        username: str,
        columns: List[JobColumnInfo],
        image_formatter: ImageFormatter,
    ) -> None:
        self.width = width
        self._username = username
        self._columns = columns
        self._image_formatter = image_formatter

    def __call__(self, jobs: Iterable[JobDescription]) -> Iterator[str]:
        rows: List[List[str]] = []
        rows.append([column.title for column in self._columns])
        for job in jobs:
            rows.append(
                TabularJobRow.from_job(
                    job, self._username, image_formatter=self._image_formatter
                ).to_list(self._columns)
            )
        for line in table(
            rows,
            widths=[column.width for column in self._columns],
            aligns=[column.align for column in self._columns],
            max_width=self.width if self.width else None,
        ):
            yield line


class ResourcesFormatter:
    def __call__(self, resources: Resources) -> str:
        lines = list()
        lines.append("Memory: " + format_size(resources.memory_mb * 1024 ** 2))
        lines.append(f"CPU: {resources.cpu:0.1f}")
        if resources.gpu:
            lines.append(f"GPU: {resources.gpu:0.1f} x {resources.gpu_model}")

        if resources.tpu_type:
            lines.append(f"TPU: {resources.tpu_type}/{resources.tpu_software_version}")

        additional = list()
        if resources.shm:
            additional.append("Extended SHM space")

        if additional:
            lines.append(f'Additional: {",".join(additional)}')

        indent = "  "
        return "Resources:\n" + indent + f"\n{indent}".join(lines)


class JobStartProgress:
    @classmethod
    def create(cls, tty: bool, color: bool, quiet: bool) -> "JobStartProgress":
        if quiet:
            return JobStartProgress()
        elif tty:
            return DetailedJobStartProgress(color)
        return StreamJobStartProgress()

    def __call__(self, job: JobDescription) -> None:
        pass

    def close(self) -> None:
        pass

    def _get_status_reason_message(self, job: JobDescription) -> str:
        if job.history.reason:
            return job.history.reason
        elif job.status == JobStatus.PENDING:
            return "Initializing"
        return ""

    def _get_status_description_message(self, job: JobDescription) -> str:
        description = job.history.description or ""
        if description:
            return f"({description})"
        return ""


class DetailedJobStartProgress(JobStartProgress):
    def __init__(self, color: bool):
        self._time = time.time()
        self._color = color
        self._prev = ""
        if sys.platform == "win32":
            self._spinner = itertools.cycle("-\\|/")
        else:
            self._spinner = itertools.cycle("◢◣◤◥")
        self._printer = TTYPrinter()
        self._lineno = 0

    def __call__(self, job: JobDescription) -> None:
        new_time = time.time()
        dt = new_time - self._time
        msg = "Status: " + format_job_status(job.status)
        reason = self._get_status_reason_message(job)
        if reason:
            msg += " " + style(reason, bold=True)
        description = self._get_status_description_message(job)
        if description:
            msg += " " + description

        if not self._color:
            msg = unstyle(msg)
        if msg != self._prev:
            if self._prev:
                self._printer.print(self._prev, lineno=self._lineno)
            self._prev = msg
            self._lineno = self._printer.total_lines
            self._printer.print(msg)
        else:
            self._printer.print(
                f"{msg} {next(self._spinner)} [{dt:.1f} sec]", lineno=self._lineno
            )


class StreamJobStartProgress(JobStartProgress):
    def __init__(self) -> None:
        self._printer = StreamPrinter()
        self._prev = ""

    def __call__(self, job: JobDescription) -> None:
        msg = f"Status: {job.status}"
        reason = self._get_status_reason_message(job)
        if reason:
            msg += " " + reason
        description = self._get_status_description_message(job)
        if description:
            msg += " " + description

        if msg != self._prev:
            self._printer.print(msg)
            self._prev = msg
        else:
            self._printer.tick()
