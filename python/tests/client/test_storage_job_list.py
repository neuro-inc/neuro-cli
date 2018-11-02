from typing import List

import pytest

from neuromation.cli.command_handlers import JobHandlerOperations
from neuromation.client.jobs import JobDescription, JobStatusHistory


@pytest.fixture
def jobs_mock(mocked_jobs):
    def job_list() -> List[JobDescription]:
        jobs = [
            JobDescription(
                status="pending",
                id="id0-pending-new",
                client=None,
                image="ubuntu",
                command="shell",
                history=JobStatusHistory(
                    status="pending",
                    reason="",
                    description="",
                    created_at="2019-09-25T12:28:21.298672+00:00",
                    started_at="",
                    finished_at="",
                ),
            ),
            JobDescription(
                status="pending",
                id="id0-pending-mid",
                client=None,
                image="ubuntu",
                command="shell",
                history=JobStatusHistory(
                    status="pending",
                    reason="",
                    description="",
                    created_at="2018-11-25T12:28:21.298672+00:00",
                    started_at="",
                    finished_at="",
                ),
            ),
            JobDescription(
                status="running",
                id="id0-running-old",
                client=None,
                image="ubuntu",
                command="shell",
                history=JobStatusHistory(
                    status="running",
                    reason="",
                    description="",
                    created_at="2018-09-25T12:28:21.298672+00:00",
                    started_at="",
                    finished_at="",
                ),
            ),
        ]
        return jobs

    def jobs_status(id) -> JobDescription:
        return JobDescription(
            status="running", id=id, client=None, image="ubuntu", command="shell"
        )

    mock = mocked_jobs
    mock.list = job_list
    mock.status = jobs_status

    def mock_():
        return mock

    return mock_


class TestJobListFilter:
    def test_job_filter_all(self, jobs_mock):
        jobs = JobHandlerOperations("test-user").list_jobs(None, jobs_mock)
        assert jobs

    def test_job_filter_running(self, jobs_mock):
        jobs = JobHandlerOperations("test-user").list_jobs("running", jobs_mock)
        assert jobs

    def test_job_filter_failed(self, jobs_mock):
        jobs = JobHandlerOperations("test-user").list_jobs("failed", jobs_mock)
        assert not jobs


class TestJobListSort:
    def test_sort(self, jobs_mock):
        jobs = JobHandlerOperations("test-user").list_jobs(None, jobs_mock)
        assert jobs.index("id0-pending-new") > jobs.index("id0-running-old")

    def test_sort_filter(self, jobs_mock):
        jobs = JobHandlerOperations("test-user").list_jobs("pending", jobs_mock)
        assert jobs.index("id0-pending-new") > jobs.index("id0-pending-mid")


def test_job_status_query(jobs_mock):
    jobs = JobHandlerOperations("test-user").status("id0", jobs_mock)
    assert jobs == JobDescription(
        status="running", id="id0", client=None, image="ubuntu", command="shell"
    )
