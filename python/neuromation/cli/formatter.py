import itertools
import re
import time
from typing import Iterable, Optional

import click
from dateutil.parser import isoparse  # type: ignore

from neuromation.client import JobDescription, JobStatus, Resources
from neuromation.client.jobs import JobTelemetry

from .rc import Config


BEFORE_PROGRESS = "\r"
AFTER_PROGRESS = "\n"
CLEAR_LINE_TAIL = "\033[0K"


# Do nasty hack click to fix unstyle problem
def _patch_click() -> None:
    import click._compat  # type: ignore

    _ansi_re = re.compile(r"\033\[([;\?0-9]*)([a-zA-Z])")
    click._compat._ansi_re = _ansi_re


_patch_click()
del _patch_click


COLORS = {
    JobStatus.PENDING: "yellow",
    JobStatus.RUNNING: "blue",
    JobStatus.SUCCEEDED: "green",
    JobStatus.FAILED: "red",
    JobStatus.UNKNOWN: "yellow",
}


def format_job_status(status: JobStatus) -> str:
    return click.style(status.value, fg=COLORS.get(status, "reset"))


class BaseFormatter:
    def _truncate_string(self, input: Optional[str], max_length: int) -> str:
        if input is None:
            return ""
        if len(input) <= max_length:
            return input
        len_tail, placeholder = 3, "..."
        if max_length < len_tail or max_length < len(placeholder):
            return placeholder
        tail = input[-len_tail:] if max_length > len(placeholder) + len_tail else ""
        index_stop = max_length - len(placeholder) - len(tail)
        return input[:index_stop] + placeholder + tail

    def _wrap(self, text: Optional[str]) -> str:
        return "'" + (text or "") + "'"


class JobFormatter(BaseFormatter):
    def __init__(self, quiet: bool = True) -> None:
        self._quiet = quiet

    def __call__(self, job: JobDescription) -> str:
        job_id = click.style(job.id, bold=True)
        if self._quiet:
            return job_id
        return (
            f"Job ID: {job_id} Status: {format_job_status(job.status)}\n"
            + f"Shortcuts:\n"
            + f"  neuro job status {job.id}  # check job status\n"
            + f"  neuro job monitor {job.id} # monitor job stdout\n"
            + f"  neuro job top {job.id}     # display real-time job telemetry\n"
            + f"  neuro job kill {job.id}    # kill job"
        )


class JobStartProgress(BaseFormatter):
    SPINNER = ("|", "/", "-", "\\")

    def __init__(self, color: bool) -> None:
        self._color = color
        self._time = time.time()
        self._spinner = itertools.cycle(self.SPINNER)
        self._last_size = 0

    def __call__(self, job: JobDescription, *, finish: bool = False) -> str:
        if not self._color:
            return ""
        new_time = time.time()
        dt = new_time - self._time
        txt_status = format_job_status(job.status)
        if job.history.reason:
            reason = " " + click.style(job.history.reason, bold=True)
        else:
            reason = ""
        ret = BEFORE_PROGRESS + f"\rStatus: {txt_status}{reason} [{dt:.1f} sec]"
        if not finish:
            ret += " " + next(self._spinner)
        ret += CLEAR_LINE_TAIL
        if finish:
            ret += AFTER_PROGRESS
        return ret


class JobStatusFormatter(BaseFormatter):
    def __call__(self, job_status: JobDescription) -> str:
        result: str = f"Job: {job_status.id}\n"
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

        if job_status.http_url:
            result = f"{result}Http URL: {job_status.http_url}\n"
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
        if job_status.status == JobStatus.FAILED:
            result += "\n===Description===\n"
            result += f"{job_status.history.description}\n================="
        return result


class JobTelemetryFormatter(BaseFormatter):
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


class JobListFormatter(BaseFormatter):
    def __init__(self, quiet: bool = False):
        self.quiet = quiet
        self.tab = "\t"
        self.column_lengths = {
            "id": 40,
            "status": 10,
            "image": 15,
            "description": 50,
            "command": 50,
        }

    def __call__(self, jobs: Iterable[JobDescription], description: str = "") -> str:
        if description:
            jobs = [j for j in jobs if j.description == description]

        jobs = sorted(jobs, key=lambda j: isoparse(j.history.created_at))
        lines = list()
        if not self.quiet:
            lines.append(self._format_header_line())
        lines.extend(map(self._format_job_line, jobs))
        return "\n".join(lines)

    def _format_header_line(self) -> str:
        return self.tab.join(
            [
                "ID".ljust(self.column_lengths["id"]),
                "STATUS".ljust(self.column_lengths["status"]),
                "IMAGE".ljust(self.column_lengths["image"]),
                "DESCRIPTION".ljust(self.column_lengths["description"]),
                "COMMAND".ljust(self.column_lengths["command"]),
            ]
        )

    def _format_job_line(self, job: JobDescription) -> str:
        def truncate_then_wrap(value: str, key: str) -> str:
            return self._wrap(self._truncate_string(value, self.column_lengths[key]))

        if self.quiet:
            return job.id.ljust(self.column_lengths["id"])

        description = truncate_then_wrap(job.description or "", "description")
        command = truncate_then_wrap(job.container.command or "", "command")
        return self.tab.join(
            [
                job.id.ljust(self.column_lengths["id"]),
                job.status.ljust(self.column_lengths["status"]),
                job.container.image.ljust(self.column_lengths["image"]),
                description.ljust(self.column_lengths["description"]),
                command.ljust(self.column_lengths["command"]),
            ]
        )


class ResourcesFormatter(BaseFormatter):
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


class ConfigFormatter:
    def __call__(self, config: Config) -> str:
        lines = []
        lines.append(f"User Name: {config.get_platform_user_name()}")
        lines.append(f"API URL: {config.url}")
        lines.append(f"Docker Registry URL: {config.registry_url}")
        lines.append(f"Github RSA Path: {config.github_rsa_path}")
        indent = "  "
        return "Config:\n" + indent + f"\n{indent}".join(lines)
