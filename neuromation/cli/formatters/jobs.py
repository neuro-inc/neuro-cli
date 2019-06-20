import abc
import datetime
import itertools
import time
from dataclasses import dataclass
from math import floor
from sys import platform
from typing import Iterable, Iterator, List, Mapping

import humanize
from click import style, unstyle
from dateutil.parser import isoparse

from neuromation.api import (
    ImageNameParser,
    JobDescription,
    JobStatus,
    JobTelemetry,
    Resources,
)
from neuromation.cli.printer import StreamPrinter, TTYPrinter


COLORS = {
    JobStatus.PENDING: "yellow",
    JobStatus.RUNNING: "blue",
    JobStatus.SUCCEEDED: "green",
    JobStatus.FAILED: "red",
    JobStatus.UNKNOWN: "yellow",
}


def format_job_status(status: JobStatus) -> str:
    return style(status.value, fg=COLORS.get(status, "reset"))


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
        http_url = job.http_url_named or job.http_url
        if http_url:
            out.append(style("Http URL", bold=True) + f": {http_url}")
        out.append(style("Shortcuts", bold=True) + ":")

        out.append(
            f"  neuro status {job_alias}  " + style("# check job status", dim=True)
        )
        out.append(
            f"  neuro logs {job_alias}    " + style("# monitor job stdout", dim=True)
        )
        out.append(
            f"  neuro top {job_alias}     "
            + style("# display real-time job telemetry", dim=True)
        )
        out.append(f"  neuro kill {job_alias}    " + style("# kill job", dim=True))
        return "\n".join(out)


class JobStatusFormatter:
    def __call__(self, job_status: JobDescription) -> str:
        result: str = f"Job: {job_status.id}\n"
        if job_status.name:
            result += f"Name: {job_status.name}\n"
        result += f"Owner: {job_status.owner if job_status.owner else ''}\n"
        if job_status.description:
            result += f"Description: {job_status.description}\n"
        result += f"Status: {job_status.status}"
        if (
            job_status.history
            and job_status.history.reason
            and job_status.status in [JobStatus.FAILED, JobStatus.PENDING]
        ):
            result += f" ({job_status.history.reason})"
        result += f"\nImage: {job_status.container.image}\n"

        result += f"Command: {job_status.container.command}\n"
        resource_formatter = ResourcesFormatter()
        result += resource_formatter(job_status.container.resources) + "\n"
        result += f"Preemptible: {job_status.is_preemptible}\n"
        if job_status.internal_hostname:
            result += f"Internal Hostname: {job_status.internal_hostname}\n"
        http_url = job_status.http_url_named or job_status.http_url
        if http_url:
            result = f"{result}Http URL: {http_url}\n"
        if job_status.container.http:
            result = (
                f"{result}Http authentication: "
                f"{job_status.container.http.requires_auth}\n"
            )
        if job_status.container.env:
            result += f"Environment:\n"
            for key, value in job_status.container.env.items():
                result += f"{key}={value}\n"

        assert job_status.history
        result = f"{result}Created: {job_status.history.created_at}"
        if job_status.status in [
            JobStatus.RUNNING,
            JobStatus.FAILED,
            JobStatus.SUCCEEDED,
        ]:
            result += "\n" f"Started: {job_status.history.started_at}"
        if job_status.status in [JobStatus.FAILED, JobStatus.SUCCEEDED]:
            result += "\n" f"Finished: {job_status.history.finished_at}"
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
    status: str
    when: str
    image: str
    description: str
    command: str

    @classmethod
    def from_job(
        cls, job: JobDescription, image_parser: ImageNameParser
    ) -> "TabularJobRow":
        image_normalized = image_parser.normalize(job.container.image)
        if job.status == JobStatus.PENDING:
            when = job.history.created_at
        elif job.status == JobStatus.RUNNING:
            when = job.history.started_at
        else:
            when = job.history.finished_at
        when_datetime = datetime.datetime.fromtimestamp(isoparse(when).timestamp())
        if time.time() - when_datetime.timestamp() < 60 * 60 * 24:
            when_humanized = humanize.naturaltime(when_datetime)
        else:
            when_humanized = humanize.naturaldate(when_datetime)
        return cls(
            id=job.id,
            name=job.name if job.name else "",
            status=job.status,
            when=when_humanized,
            image=image_normalized,
            description=job.description if job.description else "",
            command=job.container.command if job.container.command else "",
        )


class TabularJobsFormatter(BaseJobsFormatter):
    def __init__(self, width: int, image_parser: ImageNameParser):
        self.width = width
        self.column_length: Mapping[str, List[int]] = {
            "id": [2, 40],
            "name": [2, 40],
            "status": [6, 10],
            "when": [4, 15],
            "image": [5, 15],
            "description": [11, 50],
            "command": [7, 0],
        }
        self.image_parser = image_parser

    def _positions(self, rows: Iterable[TabularJobRow]) -> Mapping[str, int]:
        positions = {}
        position = 0
        for name in self.column_length:
            if rows:
                sorted_length = sorted(
                    [len(getattr(row, name)) for row in rows], reverse=True
                )
                n90 = floor(len(sorted_length) / 10)
                length = sorted_length[n90]
                if self.column_length[name][0]:
                    length = max(length, self.column_length[name][0])
                if self.column_length[name][1]:
                    length = min(length, self.column_length[name][1])
            else:
                length = self.column_length[name][0]
            positions[name] = position
            position += 2 + length
        return positions

    def __call__(self, jobs: Iterable[JobDescription]) -> Iterator[str]:
        rows: List[TabularJobRow] = []
        for job in jobs:
            rows.append(TabularJobRow.from_job(job, self.image_parser))
        header = TabularJobRow(
            id="ID",
            name="NAME",
            status="STATUS",
            when="WHEN",
            image="IMAGE",
            description="DESCRIPTION",
            command="COMMAND",
        )
        positions = self._positions(rows)
        for row in [header] + rows:
            line = ""
            for name in positions.keys():
                value = getattr(row, name)
                if line:
                    position = positions[name]
                    if len(line) > position - 2:
                        line += "  " + value
                    else:
                        line = line.ljust(position) + value
                else:
                    line = value
            if self.width:
                line = line[: self.width]
            yield line


class ResourcesFormatter:
    def __call__(self, resources: Resources) -> str:
        lines = list()
        lines.append(f"Memory: {resources.memory_mb} MB")
        lines.append(f"CPU: {resources.cpu:0.1f}")
        if resources.gpu:
            lines.append(f"GPU: {resources.gpu:0.1f} x {resources.gpu_model}")

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


class DetailedJobStartProgress(JobStartProgress):
    def __init__(self, color: bool):
        self._time = time.time()
        self._color = color
        self._prev = ""
        if platform == "win32":
            self._spinner = itertools.cycle("-\\|/")
        else:
            self._spinner = itertools.cycle("◢◣◤◥")
        self._printer = TTYPrinter()
        self._lineno = 0

    def __call__(self, job: JobDescription) -> None:
        new_time = time.time()
        dt = new_time - self._time
        msg = "Status: " + format_job_status(job.status)
        if job.history.reason:
            reason = job.history.reason
        elif job.status == JobStatus.PENDING:
            reason = "Initializing"
        else:
            reason = ""
        if reason:
            msg += " " + style(reason, bold=True)
        if not self._color:
            msg = unstyle(msg)
        if msg != self._prev:
            if self._prev:
                self._printer.print(self._prev, lineno=self._lineno)
            self._prev = msg
            self._printer.print(msg)
            self._lineno = self._printer.total_lines
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
        if job.history.reason:
            reason = job.history.reason
        elif job.status == JobStatus.PENDING:
            reason = "Initializing"
        else:
            reason = ""
        if reason:
            msg += " " + reason
        if msg != self._prev:
            self._printer.print(msg)
            self._prev = msg
        else:
            self._printer.tick()
