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
    def _format_job_id(cls, job: Optional[JobDescription]):
        length = 40
        return f"{(job.id if job else 'ID'):<{length}}"

    @classmethod
    def _format_job_status(cls, job: Optional[JobDescription]):
        length = 10
        return f"{(job.status if job else 'STATUS'):<{length}}"

    @classmethod
    def _format_job_image(cls, job: Optional[JobDescription]):
        length = 15
        return f"{(job.image if job else 'IMAGE'):<{length}}"

    @classmethod
    def _format_job_description(cls, job: Optional[JobDescription]):
        length = 50
        default = "DESCRIPTION"
        line = cls._wrap(cls._truncate(job.description, length - 2)) if job else default
        return f"{line:<{length}}"

    @classmethod
    def _format_job_command(cls, job: Optional[JobDescription]):
        length = 50
        line = cls._wrap(cls._truncate(job.command, length - 2)) if job else "COMMAND"
        return f"{line:<{length}}"

    def _format_job_job_line_list(self, job: Optional[JobDescription]) -> str:
        line_list = [self._format_job_id(job)]
        if not self.quiet:
            line_list.extend(
                [
                    self._format_job_status(job),
                    self._format_job_image(job),
                    self._format_job_description(job),
                    self._format_job_command(job),
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
