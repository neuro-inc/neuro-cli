from typing import Iterable, Optional, Union

from neuromation.client.jobs import JobDescription, JobItem, JobStatus


class OutputFormatter:
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


class JobStatusFormatter:
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


class JobListFormatter:
    def __init__(self, quiet: bool = False):
        self.quiet = quiet
        self.tab = "\t"

    @classmethod
    def _wrap(cls, text: str) -> str:
        return f"'{(text if text is not None else '')}'"

    @classmethod
    def _truncate(cls, input: Optional[str], max_length: int) -> str:
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
    def _format_short(cls, job: Optional[JobDescription], member: str, length: int):
        value = (job.__getattribute__(member) or "") if job else member.upper()
        return f"{value:<{length}}"

    @classmethod
    def _format_long(cls, job: Optional[JobDescription], member: str, length: int):
        if job:
            member = job.__getattribute__(member) or ""
            value = cls._wrap(cls._truncate(member, length - 2))
        else:
            value = member.upper()
        return f"{value:<{length}}"

    def _format_job_job_line_list(self, job: Optional[JobDescription]) -> str:
        line_list = [self._format_short(job, "id", 40)]
        if not self.quiet:
            line_list.extend(
                [
                    self._format_short(job, "status", 10),
                    self._format_short(job, "image", 15),
                    self._format_long(job, "description", 50),
                    self._format_long(job, "command", 50),
                ]
            )
        return self.tab.join(line_list)

    def _format_job_line(self, job: JobDescription) -> str:
        return self._format_job_job_line_list(job)

    def _format_header_line(self) -> str:
        return self._format_job_job_line_list(None)

    def format_jobs(self, jobs: Iterable[JobDescription]) -> str:
        lines = list()
        if not self.quiet:
            lines.append(self._format_header_line())
        lines.extend(map(self._format_job_line, jobs))
        return "\n".join(lines)
