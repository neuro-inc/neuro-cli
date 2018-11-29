from unittest.mock import MagicMock

import pytest

from neuromation import JobItem
from neuromation.cli.formatter import (
    BaseFormatter,
    JobListFormatter,
    JobStatusFormatter,
    OutputFormatter,
)
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
            owner="test-user",
            id="test-job",
            description="test job description",
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
            status == "Job: test-job\n"
            "Owner: test-user\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            "Resources: None\n"
            "Http URL: http://local.host.test/\n"
            "Created: NOW\nStarted: NOW1\nFinished: NOW2\n"
            "===Description===\n"
            "ErrorDesc\n================="
        )

    def test_pending_job_no_reason(self) -> None:
        description = JobDescription(
            status=JobStatus.PENDING,
            id="test-job",
            description="test job description",
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
            status == "Job: test-job\n"
            "Owner: \n"
            "Description: test job description\n"
            "Status: pending\n"
            "Image: test-image\n"
            "Command: test-command\n"
            "Resources: None\n"
            "Created: NOW"
        )

    def test_pending_job_with_reason(self) -> None:
        description = JobDescription(
            status=JobStatus.PENDING,
            id="test-job",
            description="test job description",
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
            status == "Job: test-job\n"
            "Owner: \n"
            "Description: test job description\n"
            "Status: pending (ContainerCreating)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            "Resources: None\n"
            "Created: NOW"
        )

    def test_pending_job_no_description(self) -> None:
        description = JobDescription(
            status=JobStatus.PENDING,
            id="test-job",
            description=None,
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
            status == "Job: test-job\n"
            "Owner: \n"
            "Status: pending (ContainerCreating)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            "Resources: None\n"
            "Created: NOW"
        )


class TestBaseFormatter:
    def test_truncate_string(self):
        truncate = BaseFormatter()._truncate_string
        assert truncate(None, 15) == ""
        assert truncate("", 15) == ""
        assert truncate("not truncated", 15) == "not truncated"
        assert truncate("A" * 10, 1) == "..."
        assert truncate("A" * 10, 3) == "..."
        assert truncate("A" * 10, 5) == "AA..."
        assert truncate("A" * 6, 5) == "AA..."
        assert truncate("A" * 7, 5) == "AA..."
        assert truncate("A" * 10, 10) == "A" * 10
        assert truncate("A" * 15, 10) == "A" * 4 + "..." + "A" * 3


class TestJobListFormatter:
    quiet = JobListFormatter(quiet=True)
    loud = JobListFormatter(quiet=False)

    def test_header_line_quiet(self):
        assert self.quiet._format_header_line() == f"{'ID':<40}"

    def test_header_line_non_quiet(self):
        expected = "\t".join(
            [
                f"{'ID':<40}",
                f"{'STATUS':<10}",
                f"{'IMAGE':<15}",
                f"{'DESCRIPTION':<50}",
                f"{'COMMAND':<50}",
            ]
        )
        assert self.loud._format_header_line() == expected

    @pytest.mark.parametrize("number_of_jobs", [0, 1, 2, 10, 10_000])
    def test_format_jobs_quiet(self, number_of_jobs):
        jobs = [
            JobDescription(
                status=JobStatus.RUNNING,
                id=f"test-job-{index}",
                description=f"test-description-{index}",
                client=None,
                image=f"test-image-{index}",
                command=f"test-command-{index}",
                history=JobStatusHistory(
                    status=JobStatus.PENDING,
                    reason="ContainerCreating",
                    description=None,
                    created_at="NOW",
                    started_at=None,
                    finished_at=None,
                ),
            )
            for index in range(number_of_jobs)
        ]

        def format_expected_job_line(index):
            return f"test-job-{index}".ljust(40)

        expected = "\n".join(
            [format_expected_job_line(index) for index in range(number_of_jobs)]
        )
        assert self.quiet.format_jobs(jobs) == expected, expected

    @pytest.mark.parametrize("number_of_jobs", [0, 1, 2, 10, 10_000])
    def test_format_jobs_non_quiet(self, number_of_jobs):
        jobs = [
            JobDescription(
                status=JobStatus.RUNNING,
                id=f"test-job-{index}",
                description=f"test-description-{index}",
                client=None,
                image=f"test-image-{index}",
                command=f"test-command-{index}",
                history=JobStatusHistory(
                    status=JobStatus.PENDING,
                    reason="ContainerCreating",
                    description=None,
                    created_at="NOW",
                    started_at=None,
                    finished_at=None,
                ),
            )
            for index in range(number_of_jobs)
        ]

        def format_expected_job_line(index):
            return "\t".join(
                [
                    f"test-job-{index}".ljust(40),
                    f"running".ljust(10),
                    f"test-image-{index}".ljust(15),
                    f"'test-description-{index}'".ljust(50),
                    f"'test-command-{index}'".ljust(50),
                ]
            )

        expected = "\n".join(
            [self.loud._format_header_line()]
            + [format_expected_job_line(index) for index in range(number_of_jobs)]
        )
        assert self.loud.format_jobs(jobs) == expected, expected
