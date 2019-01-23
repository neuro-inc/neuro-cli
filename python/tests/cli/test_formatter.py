import pytest
from yarl import URL

from neuromation.cli.formatter import (
    BaseFormatter,
    JobListFormatter,
    JobStatusFormatter,
    OutputFormatter,
    ResourcesFormatter,
    StorageLsFormatter,
)
from neuromation.clientv2 import (
    Container,
    FileStatus,
    JobDescription,
    JobStatus,
    JobStatusHistory,
    Resources,
)


TEST_JOB_STATUS = "pending"
TEST_JOB_ID = "job-ad09fe07-0c64-4d32-b477-3b737d215621"


@pytest.fixture
def job_descr():
    return JobDescription(
        status=TEST_JOB_STATUS,
        id=TEST_JOB_ID,
        owner="owner",
        history=JobStatusHistory(
            status=JobStatus.PENDING,
            reason="ErrorReason",
            description="ErrorDesc",
            created_at="2018-09-25T12:28:21.298672+00:00",
            started_at="2018-09-25T12:28:59.759433+00:00",
            finished_at="2018-09-25T12:28:59.759433+00:00",
        ),
        container=Container(
            image="ubuntu:latest", resources=Resources.create(0.1, 0, None, None, False)
        ),
        ssh_auth_server="ssh-auth",        
        is_preemptible=True,
    )


class TestOutputFormatter:
    def test_quiet(self, job_descr):
        assert OutputFormatter.format_job(job_descr, quiet=True) == TEST_JOB_ID

    def test_non_quiet(self, job_descr) -> None:
        expected = (
            f"Job ID: {TEST_JOB_ID} Status: {TEST_JOB_STATUS}\n"
            + f"Shortcuts:\n"
            + f"  neuro job status {TEST_JOB_ID}  # check job status\n"
            + f"  neuro job monitor {TEST_JOB_ID} # monitor job stdout\n"
            + f"  neuro job kill {TEST_JOB_ID}    # kill job"
        )
        assert OutputFormatter.format_job(job_descr, quiet=False) == expected


class TestJobOutputFormatter:
    def test_pending_job(self) -> None:
        description = JobDescription(
            status=JobStatus.FAILED,
            owner="test-user",
            id="test-job",
            description="test job description",
            http_url=URL("http://local.host.test/"),
            ssh_server=URL("ssh://local.host.test:22/"),
            history=JobStatusHistory(
                status=JobStatus.PENDING,
                reason="ErrorReason",
                description="ErrorDesc",
                created_at="2018-09-25T12:28:21.298672+00:00",
                started_at="2018-09-25T12:28:59.759433+00:00",
                finished_at="2018-09-25T12:28:59.759433+00:00",
            ),
            container=Container(
                command="test-command",
                image="test-image",
                resources=Resources.create(0.1, 0, None, None, False),
            ),
            ssh_auth_server="ssh-auth",            
            is_preemptible=True,
        )

        status = JobStatusFormatter.format_job_status(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Owner: test-user\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource_formatter.format_resources(description.container.resources)}\n"
            "Http URL: http://local.host.test/\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "===Description===\n"
            "ErrorDesc\n================="
        )

    def test_pending_job_no_reason(self) -> None:
        description = JobDescription(
            status=JobStatus.PENDING,
            id="test-job",
            description="test job description",
            history=JobStatusHistory(
                status=JobStatus.PENDING,
                reason=None,
                description=None,
                created_at="2018-09-25T12:28:21.298672+00:00",
                started_at=None,
                finished_at=None,
            ),
            container=Container(
                command="test-command",
                image="test-image",
                resources=Resources.create(0.1, 0, None, None, False),
            ),
            ssh_auth_server="ssh-auth",            
            is_preemptible=True,
            owner="owner",
        )

        status = JobStatusFormatter.format_job_status(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Owner: owner\n"
            "Description: test job description\n"
            "Status: pending\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource_formatter.format_resources(description.container.resources)}\n"
            "Created: 2018-09-25T12:28:21.298672+00:00"
        )

    def test_pending_job_with_reason(self) -> None:
        description = JobDescription(
            status=JobStatus.PENDING,
            id="test-job",
            description="test job description",
            history=JobStatusHistory(
                status=JobStatus.PENDING,
                reason="ContainerCreating",
                description=None,
                created_at="2018-09-25T12:28:21.298672+00:00",
                started_at=None,
                finished_at=None,
            ),
            container=Container(
                image="test-image",
                command="test-command",
                resources=Resources.create(0.1, 0, None, None, False),
            ),
            ssh_auth_server="ssh-auth",            
            is_preemptible=True,
            owner="owner",
        )

        status = JobStatusFormatter.format_job_status(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Owner: owner\n"
            "Description: test job description\n"
            "Status: pending (ContainerCreating)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource_formatter.format_resources(description.container.resources)}\n"
            "Created: 2018-09-25T12:28:21.298672+00:00"
        )

    def test_pending_job_no_description(self) -> None:
        description = JobDescription(
            status=JobStatus.PENDING,
            id="test-job",
            description=None,
            history=JobStatusHistory(
                status=JobStatus.PENDING,
                reason="ContainerCreating",
                description=None,
                created_at="2018-09-25T12:28:21.298672+00:00",
                started_at=None,
                finished_at=None,
            ),
            container=Container(
                image="test-image",
                command="test-command",
                resources=Resources.create(0.1, 0, None, None, False),
            ),
            ssh_auth_server="ssh-auth",            
            is_preemptible=True,
            owner="owner",
        )

        status = JobStatusFormatter.format_job_status(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Owner: owner\n"
            "Status: pending (ContainerCreating)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource_formatter.format_resources(description.container.resources)}\n"
            "Created: 2018-09-25T12:28:21.298672+00:00"
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

    def test_wrap_string(self):
        wrap = BaseFormatter()._wrap
        assert wrap("123") == "'123'"
        assert wrap(" ") == "' '"
        assert wrap("") == "''"
        assert wrap(None) == "''"
        assert wrap(r"\0") == "'\\0'"


class TestJobListFormatter:
    quiet = JobListFormatter(quiet=True)
    loud = JobListFormatter(quiet=False)

    def test_header_line_quiet_and_non_quiet(self):
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
        assert self.quiet._format_header_line() == expected

    @pytest.mark.parametrize("number_of_jobs", [0, 1, 2, 10, 10000])
    def test_format_jobs_quiet(self, number_of_jobs):
        jobs = [
            JobDescription(
                status=JobStatus.RUNNING,
                id=f"test-job-{index}",
                description=f"test-description-{index}",
                history=JobStatusHistory(
                    status=JobStatus.PENDING,
                    reason="ContainerCreating",
                    description=None,
                    created_at="2018-09-25T12:28:21.298672+00:00",
                    started_at=None,
                    finished_at=None,
                ),
                container=Container(
                    image=f"test-image-{index}",
                    command=f"test-command-{index}",
                    resources=Resources.create(0.1, 0, None, None, False),
                ),
                ssh_auth_server="ssh-auth",
                is_preemptible=True,
                owner="owner",
            )
            for index in range(number_of_jobs)
        ]

        def format_expected_job_line(index):
            return f"test-job-{index}".ljust(40)

        expected = "\n".join(
            [format_expected_job_line(index) for index in range(number_of_jobs)]
        )
        assert self.quiet.format_jobs(jobs) == expected, expected

    @pytest.mark.parametrize("number_of_jobs", [0, 1, 2, 10, 100, 1000])
    def test_format_jobs_non_quiet(self, number_of_jobs):
        jobs = [
            JobDescription(
                status=JobStatus.RUNNING,
                id=f"test-job-{index}",
                description=f"test-description-{index}",
                history=JobStatusHistory(
                    status=JobStatus.PENDING,
                    reason="ContainerCreating",
                    description=None,
                    created_at="2018-09-25T12:28:21.298672+00:00",
                    started_at=None,
                    finished_at=None,
                ),
                container=Container(
                    image=f"test-image-{index}",
                    command=f"test-command-{index}",
                    resources=Resources.create(0.1, 0, None, None, False),
                ),
                ssh_auth_server="ssh-auth",
                is_preemptible=True,
                owner="owner",
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
        assert self.loud.format_jobs(jobs) == expected

    def test_format_jobs_description_filter(self):
        jobs = [
            JobDescription(
                status=JobStatus.RUNNING,
                id=f"test-job-{index}",
                description=f"test-description-{index}",
                history=JobStatusHistory(
                    status=JobStatus.PENDING,
                    reason="ContainerCreating",
                    description=None,
                    created_at="2018-09-25T12:28:21.298672+00:00",
                    started_at=None,
                    finished_at=None,
                ),
                container=Container(
                    image=f"test-image-{index}",
                    command=f"test-command-{index}",
                    resources=Resources.create(0.1, 0, None, None, False),
                ),
                ssh_auth_server="ssh-auth",                
                is_preemptible=True,
                owner="owner",
            )
            for index in range(2)
        ]

        def format_expected_job_line(index):
            return f"test-job-{index}".ljust(40)

        expected = "\n".join([format_expected_job_line(0)])
        assert (
            self.quiet.format_jobs(jobs, description="test-description-0") == expected
        ), expected


class TestLSFormatter:
    def test_neuro_store_ls_normal(self):
        expected = (
            "file           11             file1\n"
            + "file           12             file2\n"
            + "directory      0              dir1"
        )
        assert (
            StorageLsFormatter().format_ls(
                [
                    FileStatus("file1", 11, "FILE", 2018, "read"),
                    FileStatus("file2", 12, "FILE", 2018, "write"),
                    FileStatus("dir1", 0, "DIRECTORY", 2018, "manage"),
                ]
            )
            == expected
        )

    def test_neuro_store_ls_empty(self):
        assert StorageLsFormatter().format_ls([]) == ""


class TestResourcesFormatter:
    def test_tiny_container(self) -> None:
        resources = Resources.create(
            cpu=0.1, gpu=0, gpu_model=None, memory=16, extshm=False
        )
        resource_formatter = ResourcesFormatter()
        assert (
            resource_formatter.format_resources(resources) == "Resources:\n"
            "  Memory: 16 MB\n"
            "  CPU: 0.1"
        )

    def test_gpu_container(self) -> None:
        resources = Resources.create(
            cpu=2, gpu=1, gpu_model="nvidia-tesla-p4", memory=1024, extshm=False
        )
        resource_formatter = ResourcesFormatter()
        assert (
            resource_formatter.format_resources(resources) == "Resources:\n"
            "  Memory: 1024 MB\n"
            "  CPU: 2.0\n"
            "  GPU: 1.0 x nvidia-tesla-p4"
        )

    def test_shm_container(self) -> None:
        resources = Resources.create(
            cpu=0.1, gpu=0, gpu_model=None, memory=16, extshm=True
        )
        resource_formatter = ResourcesFormatter()
        assert (
            resource_formatter.format_resources(resources) == "Resources:\n"
            "  Memory: 16 MB\n"
            "  CPU: 0.1\n"
            "  Additional: Extended SHM space"
        )
