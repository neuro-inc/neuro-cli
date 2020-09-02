import abc
import datetime
import itertools
import sys
import textwrap
import time
from dataclasses import dataclass
from typing import Iterable, Iterator, List, Optional

import humanize
from click import secho, style, unstyle

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
    JobStatus.CANCELLED: "green",
    JobStatus.FAILED: "red",
    JobStatus.UNKNOWN: "yellow",
}


if sys.platform == "win32":
    SPINNER = itertools.cycle(r"-\|/")
else:
    SPINNER = itertools.cycle("◢◣◤◥")


def bold(text: str) -> str:
    return style(text, bold=True)


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


class JobStatusFormatter:
    def __init__(self, uri_formatter: URIFormatter, width: int = 0) -> None:
        self._format_uri = uri_formatter
        self._width = width
        self._format_image = image_formatter(uri_formatter=uri_formatter)

    def __call__(self, job_status: JobDescription) -> str:
        assert job_status.history is not None
        lines = []

        def add(descr: str, value: str) -> None:
            lines.append(f"{bold(descr)}: {value}")

        add("Job", job_status.id)
        if job_status.name:
            add("Name", job_status.name)
        if job_status.tags:
            text = ", ".join(job_status.tags)
            indent = len("Tags: ")
            if self._width > indent:
                width = self._width - indent
                text = textwrap.fill(
                    text, width=width, break_long_words=False, break_on_hyphens=False
                )
                if "\n" in text:
                    text = textwrap.indent(text, " " * indent).lstrip()
            add("Tags", text)
        add("Owner", job_status.owner or "")
        add("Cluster", job_status.cluster_name)
        if job_status.description:
            add("Description", job_status.description)
        status_str = format_job_status(job_status.status)
        if job_status.history.reason and job_status.status in [
            JobStatus.FAILED,
            JobStatus.PENDING,
        ]:
            status_str += f" ({job_status.history.reason})"
        add("Status", status_str)
        add("Image", self._format_image(job_status.container.image))

        if job_status.container.entrypoint:
            add("Entrypoint", job_status.container.entrypoint)
        if job_status.container.command:
            add("Command", job_status.container.command)
        if job_status.container.working_dir:
            add("Working dir", job_status.container.working_dir)
        resource_formatter = ResourcesFormatter()
        lines.append(resource_formatter(job_status.container.resources))
        if job_status.is_preemptible:
            add("Preemptible", "True")
        if job_status.restart_policy != JobRestartPolicy.NEVER:
            add("Restart policy", job_status.restart_policy)
        if job_status.life_span is not None:
            add("Life span", format_life_span(job_status.life_span))

        add("TTY", str(job_status.container.tty))

        if job_status.container.volumes:
            rows = [
                (
                    volume.container_path,
                    self._format_uri(volume.storage_uri),
                    "READONLY" if volume.read_only else " ",
                )
                for volume in job_status.container.volumes
            ]
            lines.append(f"{bold('Volumes')}:")
            lines.extend(f"  {i}" for i in table(rows))

        if job_status.container.secret_files:
            rows2 = [
                (secret_file.container_path, self._format_uri(secret_file.secret_uri))
                for secret_file in job_status.container.secret_files
            ]
            lines.append(f"{bold('Secret files')}:")
            lines.extend(f"  {i}" for i in table(rows2))

        if job_status.internal_hostname:
            add("Internal Hostname", job_status.internal_hostname)
        if job_status.internal_hostname_named:
            add("Internal Hostname Named", job_status.internal_hostname_named)
        if job_status.http_url:
            add("Http URL", str(job_status.http_url))
        if job_status.container.http:
            add("Http port", str(job_status.container.http.port))
            add("Http authentication", str(job_status.container.http.requires_auth))
        if job_status.container.env:
            lines.append(f"{bold('Environment')}:")
            for key, value in job_status.container.env.items():
                lines.append(f"  {key}={value}")
        if job_status.container.secret_env:
            lines.append(f"{bold('Secret environment')}:")
            for key, uri in job_status.container.secret_env.items():
                lines.append(f"  {key}={self._format_uri(uri)}")

        assert job_status.history.created_at is not None
        add("Created", job_status.history.created_at.isoformat())
        if job_status.status in [
            JobStatus.RUNNING,
            JobStatus.FAILED,
            JobStatus.SUCCEEDED,
            JobStatus.CANCELLED,
        ]:
            assert job_status.history.started_at is not None
            add("Started", job_status.history.started_at.isoformat())
        if job_status.status in [
            JobStatus.CANCELLED,
            JobStatus.FAILED,
            JobStatus.SUCCEEDED,
        ]:
            assert job_status.history.finished_at is not None
            add("Finished", job_status.history.finished_at.isoformat())
            add("Exit code", str(job_status.history.exit_code))
        if job_status.status == JobStatus.FAILED and job_status.history.description:
            lines.append(bold("=== Description ==="))
            lines.append(job_status.history.description)
            lines.append("===================")
        return "\n".join(lines)


def format_life_span(life_span: Optional[float]) -> str:
    if life_span is None:
        return ""
    if life_span == 0:
        return "no limit"
    return format_timedelta(datetime.timedelta(seconds=life_span))


def format_datetime(when: Optional[datetime.datetime]) -> str:
    if when is None:
        return ""
    assert when.tzinfo is not None
    delta = datetime.datetime.now(datetime.timezone.utc) - when
    if delta < datetime.timedelta(days=1):
        return humanize.naturaltime(delta)
    else:
        return humanize.naturaldate(when.astimezone())


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
    created: str
    started: str
    finished: str
    image: str
    owner: str
    description: str
    cluster_name: str
    command: str
    life_span: str
    workdir: str

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
        return cls(
            id=bold(job.id),
            name=job.name if job.name else "",
            tags=",".join(job.tags),
            status=format_job_status(job.status),
            when=format_datetime(when),
            created=format_datetime(job.history.created_at),
            started=format_datetime(job.history.started_at),
            finished=format_datetime(job.history.finished_at),
            image=image_formatter(job.container.image),
            owner=("<you>" if job.owner == username else job.owner),
            description=job.description if job.description else "",
            cluster_name=job.cluster_name,
            command=job.container.command if job.container.command else "",
            life_span=format_life_span(job.life_span),
            workdir=job.container.working_dir or "",
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
        rows.append([bold(column.title) for column in self._columns])
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
        lines = []

        def add(descr: str, value: str) -> None:
            lines.append(f"{bold(descr)}: {value}")

        add("Memory", format_size(resources.memory_mb * 1024 ** 2))
        add("CPU", f"{resources.cpu:0.1f}")
        if resources.gpu:
            add("GPU", f"{resources.gpu:0.1f} x {resources.gpu_model}")

        if resources.tpu_type:
            add("TPU", f"{resources.tpu_type}/{resources.tpu_software_version}")

        additional = []
        if resources.shm:
            additional.append("Extended SHM space")

        if additional:
            add("Additional", ",".join(additional))

        indent = "  "
        return f"{bold('Resources')}:\n" + indent + f"\n{indent}".join(lines)


class JobStartProgress:
    time_factory = staticmethod(time.monotonic)

    @classmethod
    def create(cls, tty: bool, color: bool, quiet: bool) -> "JobStartProgress":
        if quiet:
            return JobStartProgress()
        elif tty:
            return DetailedJobStartProgress(color)
        return StreamJobStartProgress()

    def begin(self, job: JobDescription) -> None:
        # Quiet mode
        print(job.id)

    def step(self, job: JobDescription) -> None:
        pass

    def end(self, job: JobDescription) -> None:
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
        self._time = self.time_factory()
        self._color = color
        self._prev = ""
        self._spinner = SPINNER
        self._printer = TTYPrinter()
        self._lineno = 0

    def begin(self, job: JobDescription) -> None:
        self._printer.print(style("√ ", fg="green") + bold("Job ID") + f": {job.id} ")
        if job.name:
            self._printer.print(
                style("√ ", fg="green") + bold("Name") + f": {job.name}"
            )

    def step(self, job: JobDescription) -> None:
        new_time = self.time_factory()
        dt = new_time - self._time
        msg = "Status: " + format_job_status(job.status)
        reason = self._get_status_reason_message(job)
        if reason:
            msg += " " + bold(reason)
        description = self._get_status_description_message(job)
        if description:
            msg += " " + description

        if job.status == JobStatus.PENDING:
            msg = style("- ", fg="yellow") + msg
        elif job.status == JobStatus.FAILED:
            msg = style("× ", fg="red") + msg
        else:
            # RUNNING or SUCCEDED
            msg = style("√ ", fg="green") + msg

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

    def end(self, job: JobDescription) -> None:
        out = []

        if job.status != JobStatus.FAILED:
            http_url = job.http_url
            if http_url:
                out.append(style("√ ", fg="green") + bold("Http URL") + f": {http_url}")
            if job.life_span:
                limit = humanize.naturaldelta(datetime.timedelta(seconds=job.life_span))
                out.append(
                    style("√ ", fg="green")
                    + style(
                        f"The job will die in {limit}. ",
                        fg="yellow",
                    )
                    + "See --life-span option documentation for details.",
                )
            self._printer.print("\n".join(out))


class StreamJobStartProgress(JobStartProgress):
    def __init__(self) -> None:
        self._printer = StreamPrinter()
        self._prev = ""

    def begin(self, job: JobDescription) -> None:
        self._printer.print(f"Job ID: {job.id}")
        if job.name:
            self._printer.print(f"Name: {job.name}")

    def step(self, job: JobDescription) -> None:
        msg = f"Status: {job.status}"
        reason = self._get_status_reason_message(job)
        if reason:
            msg += " " + reason
        description = self._get_status_description_message(job)
        if description:
            msg += " " + description

        if job.status != JobStatus.PENDING:
            msg += "\n"

        if msg != self._prev:
            self._printer.print(msg)
            self._prev = msg
        else:
            self._printer.tick()

    def end(self, job: JobDescription) -> None:
        pass


class JobStopProgress:
    TIMEOUT = 15 * 60
    time_factory = staticmethod(time.monotonic)

    @classmethod
    def create(cls, tty: bool, color: bool, quiet: bool) -> "JobStopProgress":
        if quiet:
            return JobStopProgress()
        elif tty:
            return DetailedJobStopProgress(color)
        return StreamJobStopProgress()

    def __init__(self) -> None:
        self._time = self.time_factory()

    def kill(self, job: JobDescription) -> None:
        pass

    def detach(self, job: JobDescription) -> None:
        pass

    def step(self, job: JobDescription) -> bool:
        # return False if timeout, True otherwise
        new_time = self.time_factory()
        if new_time - self._time > self.TIMEOUT:
            self.timeout(job)
            return False
        else:
            self.tick(job)
            return True

    def tick(self, job: JobDescription) -> None:
        pass

    def timeout(self, job: JobDescription) -> None:
        pass


class DetailedJobStopProgress(JobStopProgress):
    def __init__(self, color: bool):
        super().__init__()
        self._color = color
        self._spinner = SPINNER
        self._printer = TTYPrinter()
        self._lineno = 0

    def detach(self, job: JobDescription) -> None:
        secho()
        secho("× Terminal was detached but job is still running", fg="red")
        secho("Re-attach to job:", dim=True, fg="yellow")
        secho(f"  neuro attach {job.id}", dim=True)
        secho("Check job status:", dim=True, fg="yellow")
        secho(f"  neuro status {job.id}", dim=True)
        secho("Kill job:", dim=True, fg="yellow")
        secho(f"  neuro kill {job.id}", dim=True)
        secho("Fetch job logs:", dim=True, fg="yellow")
        secho(f"  neuro logs {job.id}", dim=True)

    def kill(self, job: JobDescription) -> None:
        secho()
        secho("× Job was killed", fg="red")
        secho("Get job status:", dim=True, fg="yellow")
        secho(f"  neuro status {job.id}", dim=True)
        secho("Fetch job logs:", dim=True, fg="yellow")
        secho(f"  neuro logs {job.id}", dim=True)

    def tick(self, job: JobDescription) -> None:
        new_time = self.time_factory()
        dt = new_time - self._time

        if job.status == JobStatus.RUNNING:
            msg = (
                style("-", fg="yellow")
                + f" Wait for stop {next(self._spinner)} [{dt:.1f} sec]"
            )
        else:
            msg = style("√", fg="green") + " Stopped"

        if not self._color:
            msg = unstyle(msg)
        self._printer.print(
            msg,
            lineno=self._lineno,
        )

    def timeout(self, job: JobDescription) -> None:
        secho()
        secho("× Warning !!!", fg="red")
        secho(
            "× The attached session was disconnected but the job is still alive.",
            fg="red",
        )
        secho("Reconnect to the job:", dim=True, fg="yellow")
        secho(f"  neuro attach {job.id}", dim=True)
        secho("Terminate the job:", dim=True, fg="yellow")
        secho(f"  neuro kill {job.id}", dim=True)


class StreamJobStopProgress(JobStopProgress):
    def __init__(self) -> None:
        super().__init__()
        self._printer = StreamPrinter()
        self._printer.print("Wait for stopping")

    def detach(self, job: JobDescription) -> None:
        pass

    def kill(self, job: JobDescription) -> None:
        self._printer.print("Job was killed")

    def tick(self, job: JobDescription) -> None:
        self._printer.tick()

    def timeout(self, job: JobDescription) -> None:
        self._printer.print("")
        self._printer.print("Warning !!!")
        self._printer.print(
            "The attached session was disconnected but the job is still alive."
        )


class ExecStopProgress:
    TIMEOUT = 15
    time_factory = staticmethod(time.monotonic)

    @classmethod
    def create(cls, tty: bool, color: bool, quiet: bool) -> "ExecStopProgress":
        if quiet:
            return ExecStopProgress()
        elif tty:
            return DetailedExecStopProgress(color)
        return StreamExecStopProgress()

    def __init__(self) -> None:
        self._time = self.time_factory()

    def __call__(self, running: bool) -> bool:
        # return False if timeout, True otherwise
        new_time = self.time_factory()
        if new_time - self._time > self.TIMEOUT:
            self.timeout()
            return False
        else:
            self.tick(running)
            return True

    def tick(self, running: bool) -> None:
        pass

    def timeout(self) -> None:
        pass


class DetailedExecStopProgress(ExecStopProgress):
    def __init__(self, color: bool):
        super().__init__()
        self._color = color
        self._spinner = SPINNER
        self._printer = TTYPrinter()
        self._lineno = 0

    def tick(self, running: bool) -> None:
        new_time = self.time_factory()
        dt = new_time - self._time

        if running:
            msg = (
                style("-", fg="yellow")
                + f"Wait for stopping {next(self._spinner)} [{dt:.1f} sec]"
            )
        else:
            msg = style("√", fg="green") + " Stopped"

        self._printer.print(
            msg,
            lineno=self._lineno,
        )

    def timeout(self) -> None:
        secho()
        secho("× Warning !!!", fg="red")
        secho(
            "× The attached session was disconnected "
            "but the exec process is still alive.",
            fg="red",
        )


class StreamExecStopProgress(ExecStopProgress):
    def __init__(self) -> None:
        super().__init__()
        self._printer = StreamPrinter()
        self._printer.print("Wait for stopping")

    def tick(self, running: bool) -> None:
        self._printer.tick()

    def timeout(self) -> None:
        print()
        print("Warning !!!")
        print(
            "The attached session was disconnected "
            "but the exec process is still alive."
        )
