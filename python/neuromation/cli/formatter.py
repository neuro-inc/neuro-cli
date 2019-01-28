from typing import AbstractSet, Iterable, List, Optional

from dateutil.parser import isoparse  # type: ignore

from neuromation.client import FileStatus, JobDescription, JobStatus, Resources


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


class OutputFormatter(BaseFormatter):
    def format_job(self, job: JobDescription, quiet: bool = True) -> str:
        if quiet:
            return job.id
        return (
            f"Job ID: {job.id} Status: {job.status}\n"
            + f"Shortcuts:\n"
            + f"  neuro job status {job.id}  # check job status\n"
            + f"  neuro job monitor {job.id} # monitor job stdout\n"
            + f"  neuro job kill {job.id}    # kill job"
        )


class StorageLsFormatter(BaseFormatter):
    FORMAT = "{type:<15}{size:<15,}{name:<}".format

    def fmt_long(self, lst: List[FileStatus]) -> str:
        return "\n".join(
            self.FORMAT(type=status.type.lower(), name=status.path, size=status.size)
            for status in lst
        )


class JobStatusFormatter(BaseFormatter):
    def format_job_status(self, job_status: JobDescription) -> str:
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
        result += (
            resource_formatter.format_resources(job_status.container.resources) + "\n"
        )
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

    def format_jobs(
        self,
        jobs: Iterable[JobDescription],
        statuses: AbstractSet[str] = frozenset(),
        description: str = "",
    ) -> str:
        if statuses:
            jobs = [j for j in jobs if j.status in statuses]
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
    def format_resources(self, resources: Resources) -> str:
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
        return f"Resources:\n" + indent + f"\n{indent}".join(lines)
