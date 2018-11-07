from typing import Union

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
        result += f"Status: {job_status.status}"
        if (
            job_status.history
            and job_status.history.reason
            and job_status.status in [JobStatus.FAILED, JobStatus.PENDING]
        ):
            result += f"({job_status.history.reason})"
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
