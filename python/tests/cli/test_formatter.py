from unittest.mock import MagicMock

import pytest

from neuromation import JobItem
from neuromation.cli.formatter import JobStatusFormatter, OutputFormatter
from neuromation.client.jobs import JobDescription, JobStatus, JobStatusHistory


TEST_JOB_STATUS = "pending"
TEST_JOB_ID = "job-ad09fe07-0c64-4d32-b477-3b737d215621"


@pytest.fixture
def job_item():
    return JobItem(status=TEST_JOB_STATUS, id=TEST_JOB_ID, client=MagicMock())


class TestOutputFormatter:
    def test_quiet(self, job_item):
        assert OutputFormatter.format_job(job_item, quiet=True) == TEST_JOB_ID

    def test_non_quiet(self, job_item) -> None:
        expected = (
            f"Job ID: {TEST_JOB_ID} Status: {TEST_JOB_STATUS}\n"
            + f"Shortcuts:\n"
            + f"  neuro job status {TEST_JOB_ID}  # check job status\n"
            + f"  neuro job monitor {TEST_JOB_ID} # monitor job stdout\n"
            + f"  neuro job kill {TEST_JOB_ID}    # kill job"
        )
        assert OutputFormatter.format_job(job_item, quiet=False) == expected


class TestJobOutputFormatter:
    def test_pending_job(self) -> None:
        description = JobDescription(
            status=JobStatus.FAILED,
            id="test-job",
            client=None,
            image="test-image",
            command="test-command",
            url="http://local.host.test/",
            ssh="ssh://local.host.test:22/",
            history=JobStatusHistory(
                status=JobStatus.PENDING,
                reason="ErrorReason",
                description="ErrorDesc",
                created_at="NOW",
                started_at="NOW1",
                finished_at="NOW2",
            ),
        )

        status = JobStatusFormatter.format_job_status(description)
        assert (
            status == "Job: test-job\nStatus: failed(ErrorReason)\nImage: test-image\n"
            "Command: test-command\nResources: None\n"
            "Http URL: http://local.host.test/\n"
            "Created: NOW\nStarted: NOW1\nFinished: NOW2\n"
            "===Description===\n"
            "ErrorDesc\n================="
        )

    def test_pending_job_no_reason(self) -> None:
        description = JobDescription(
            status=JobStatus.PENDING,
            id="test-job",
            client=None,
            image="test-image",
            command="test-command",
            history=JobStatusHistory(
                status=JobStatus.PENDING,
                reason=None,
                description=None,
                created_at="NOW",
                started_at=None,
                finished_at=None,
            ),
        )

        status = JobStatusFormatter.format_job_status(description)
        assert (
            status == "Job: test-job\nStatus: pending\nImage: test-image\n"
            "Command: test-command\nResources: None\nCreated: NOW"
        )

    def test_pending_job_with_reason(self) -> None:
        description = JobDescription(
            status=JobStatus.PENDING,
            id="test-job",
            client=None,
            image="test-image",
            command="test-command",
            history=JobStatusHistory(
                status=JobStatus.PENDING,
                reason="ContainerCreating",
                description=None,
                created_at="NOW",
                started_at=None,
                finished_at=None,
            ),
        )

        status = JobStatusFormatter.format_job_status(description)
        assert (
            status
            == "Job: test-job\nStatus: pending(ContainerCreating)\nImage: test-image\n"
            "Command: test-command\nResources: None\nCreated: NOW"
        )
