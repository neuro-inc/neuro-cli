from typing import Iterable, Optional, Union

from neuromation.client.jobs import JobDescription, JobItem, JobStatus


class BaseFormatter:
    @classmethod
    def _truncate_string(cls, input: Optional[str], max_length: int) -> str:
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

    @classmethod
    def _wrap(cls, text: Optional[str]) -> str:
        return "'" + (text or "") + "'"


class OutputFormatter(BaseFormatter):
    @classmethod
    def format_job(cls, job: Union[JobItem, JobDescription], quiet: bool = True) -> str:
        if quiet:
            return job.id
        return (
            f"Job ID: {job.id} Status: {job.status}\n"
            + f"Shortcuts:\n"
            + f"  neuro job status {job.id}  # check job status\n"
            + f"  neuro job monitor {job.id} # monitor job stdout\n"
            + f"  neuro job kill {job.id}    # kill job"
        )


class JobStatusFormatter(BaseFormatter):
    @classmethod
    def format_job_status(cls, job_status: JobDescription) -> str:
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
        result += f"\nImage: {job_status.image}\n"
        result += f"Command: {job_status.command}\n"
        result += f"Resources: {job_status.resources}\n"

        if job_status.url:
            result = f"{result}Http URL: {job_status.url}\n"

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

    def format_jobs(self, jobs: Iterable[JobDescription]) -> str:
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

    def _format_job_line(self, job: Optional[JobDescription]) -> str:
        def truncate_then_wrap(value: str, key: str) -> str:
            return self._wrap(self._truncate_string(value, self.column_lengths[key]))

        if self.quiet:
            return job.id.ljust(self.column_lengths["id"])

        description = truncate_then_wrap(job.description, "description")
        command = truncate_then_wrap(job.command, "command")
        return self.tab.join(
            [
                job.id.ljust(self.column_lengths["id"]),
                job.status.ljust(self.column_lengths["status"]),
                job.image.ljust(self.column_lengths["image"]),
                description.ljust(self.column_lengths["description"]),
                command.ljust(self.column_lengths["command"]),
            ]
        )
