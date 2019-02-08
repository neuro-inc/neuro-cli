import textwrap
import time
from typing import Optional

import click
import pytest
from yarl import URL

from neuromation.cli.files_formatter import (
    FilesSorter,
    LongFilesFormatter,
    SimpleFilesFormatter,
    VerticalColumnsFilesFormatter,
)
from neuromation.cli.formatter import (
    BaseFormatter,
    ConfigFormatter,
    JobFormatter,
    JobListFormatter,
    JobStartProgress,
    JobStatusFormatter,
    JobTelemetryFormatter,
    ResourcesFormatter,
)
from neuromation.cli.login import AuthToken
from neuromation.cli.rc import Config
from neuromation.client import (
    Action,
    Container,
    FileStatus,
    FileStatusType,
    JobDescription,
    JobStatus,
    JobStatusHistory,
    JobTelemetry,
    Resources,
)


TEST_JOB_ID = "job-ad09fe07-0c64-4d32-b477-3b737d215621"


@pytest.fixture
def job_descr():
    return JobDescription(
        status=JobStatus.PENDING,
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


class TestJobFormatter:
    def test_quiet(self, job_descr):
        assert click.unstyle(JobFormatter(quiet=True)(job_descr)) == TEST_JOB_ID

    def test_non_quiet(self, job_descr) -> None:
        expected = (
            f"Job ID: {TEST_JOB_ID} Status: {JobStatus.PENDING}\n"
            + f"Shortcuts:\n"
            + f"  neuro job status {TEST_JOB_ID}  # check job status\n"
            + f"  neuro job monitor {TEST_JOB_ID} # monitor job stdout\n"
            + f"  neuro job top {TEST_JOB_ID}     # display real-time job telemetry\n"
            + f"  neuro job kill {TEST_JOB_ID}    # kill job"
        )
        assert click.unstyle(JobFormatter(quiet=False)(job_descr)) == expected


class TestJobStartProgress:
    def make_job(self, status: JobStatus, reason: Optional[str]) -> JobDescription:
        return JobDescription(
            status=status,
            owner="test-user",
            id="test-job",
            description="test job description",
            http_url=URL("http://local.host.test/"),
            ssh_server=URL("ssh://local.host.test:22/"),
            history=JobStatusHistory(
                status=status,
                reason=reason,
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
            is_preemptible=False,
        )

    def strip(self, text: str) -> str:
        return click.unstyle(text).strip()

    def test_progress(self) -> None:
        progress = JobStartProgress(True)
        assert (
            self.strip(progress(self.make_job(JobStatus.PENDING, None)))
            == "Status: pending [0.0 sec] |"
        )
        assert (
            self.strip(progress(self.make_job(JobStatus.PENDING, "ContainerCreating")))
            == "Status: pending ContainerCreating [0.0 sec] /"
        )
        assert (
            self.strip(progress(self.make_job(JobStatus.PENDING, "ContainerCreating")))
            == "Status: pending ContainerCreating [0.0 sec] -"
        )
        assert (
            self.strip(progress(self.make_job(JobStatus.SUCCEEDED, None), finish=True))
            == "Status: succeeded [0.0 sec]"
        )


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
            is_preemptible=False,
        )

        status = JobStatusFormatter()(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Owner: test-user\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource_formatter(description.container.resources)}\n"
            "Preemptible: False\n"
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

        status = JobStatusFormatter()(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Owner: owner\n"
            "Description: test job description\n"
            "Status: pending\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource_formatter(description.container.resources)}\n"
            "Preemptible: True\n"
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

        status = JobStatusFormatter()(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Owner: owner\n"
            "Description: test job description\n"
            "Status: pending (ContainerCreating)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource_formatter(description.container.resources)}\n"
            "Preemptible: True\n"
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

        status = JobStatusFormatter()(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Owner: owner\n"
            "Status: pending (ContainerCreating)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource_formatter(description.container.resources)}\n"
            "Preemptible: True\n"
            "Created: 2018-09-25T12:28:21.298672+00:00"
        )


class TestJobTelemetryFormatter:
    def _format(self, timestamp: str, cpu: str, mem: str, gpu: str, gpu_mem: str):
        return "\t".join(
            [
                f"{timestamp:<24}",
                f"{cpu:<15}",
                f"{mem:<15}",
                f"{gpu:<15}",
                f"{gpu_mem:<15}",
            ]
        )

    def test_format_header_line(self):
        line = JobTelemetryFormatter().header()
        assert line == self._format(
            timestamp="TIMESTAMP",
            cpu="CPU",
            mem="MEMORY (MB)",
            gpu="GPU (%)",
            gpu_mem="GPU_MEMORY (MB)",
        )

    def test_format_telemetry_line_no_gpu(self):
        formatter = JobTelemetryFormatter()
        # NOTE: the timestamp_str encodes the local timezone
        timestamp = 1_517_248_466.238_723_6
        timestamp_str = formatter._format_timestamp(timestamp)
        telemetry = JobTelemetry(cpu=0.12345, memory=256.123, timestamp=timestamp)
        line = JobTelemetryFormatter()(telemetry)
        assert line == self._format(
            timestamp=timestamp_str, cpu="0.123", mem="256.123", gpu="0", gpu_mem="0"
        )

    def test_format_telemetry_line_with_gpu(self):
        formatter = JobTelemetryFormatter()
        # NOTE: the timestamp_str encodes the local timezone
        timestamp = 1_517_248_466
        timestamp_str = formatter._format_timestamp(timestamp)
        telemetry = JobTelemetry(
            cpu=0.12345,
            memory=256.1234,
            timestamp=timestamp,
            gpu_duty_cycle=99,
            gpu_memory=64.5,
        )
        line = formatter(telemetry)
        assert line == self._format(
            timestamp=timestamp_str,
            cpu="0.123",
            mem="256.123",
            gpu="99",
            gpu_mem=f"64.500",
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
        assert self.quiet(jobs) == expected, expected

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
        assert self.loud(jobs) == expected

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
        assert self.quiet(jobs, description="test-description-0") == expected, expected


class TestFilesFormatter:

    files = [
        FileStatus(
            "File1",
            2048,
            FileStatusType.FILE,
            int(time.mktime(time.strptime("2018-01-01 03:00:00", "%Y-%m-%d %H:%M:%S"))),
            "read",
        ),
        FileStatus(
            "File2",
            1024,
            FileStatusType.FILE,
            int(time.mktime(time.strptime("2018-10-10 13:10:10", "%Y-%m-%d %H:%M:%S"))),
            "read",
        ),
        FileStatus(
            "File3 with space",
            1_024_001,
            FileStatusType.FILE,
            int(time.mktime(time.strptime("2019-02-02 05:02:02", "%Y-%m-%d %H:%M:%S"))),
            "read",
        ),
    ]
    folders = [
        FileStatus(
            "Folder1",
            0,
            FileStatusType.DIRECTORY,
            int(time.mktime(time.strptime("2017-03-03 06:03:03", "%Y-%m-%d %H:%M:%S"))),
            "manage",
        ),
        FileStatus(
            "1Folder with space",
            0,
            FileStatusType.DIRECTORY,
            int(time.mktime(time.strptime("2017-03-03 06:03:02", "%Y-%m-%d %H:%M:%S"))),
            "manage",
        ),
    ]
    files_and_folders = files + folders

    def test_simple_formatter(self):
        formatter = SimpleFilesFormatter()
        assert list(formatter(self.files_and_folders)) == [
            f"{file.name}" for file in self.files_and_folders
        ]

    def test_long_formatter(self):
        formatter = LongFilesFormatter(human_readable=False)
        assert list(formatter(self.files_and_folders)) == [
            "-r    2048 2018-01-01 03:00:00 File1",
            "-r    1024 2018-10-10 13:10:10 File2",
            "-r 1024001 2019-02-02 05:02:02 File3 with space",
            "dm       0 2017-03-03 06:03:03 Folder1",
            "dm       0 2017-03-03 06:03:02 1Folder with space",
        ]

        formatter = LongFilesFormatter(human_readable=True)
        assert list(formatter(self.files_and_folders)) == [
            "-r    2.0K 2018-01-01 03:00:00 File1",
            "-r    1.0K 2018-10-10 13:10:10 File2",
            "-r 1000.0K 2019-02-02 05:02:02 File3 with space",
            "dm       0 2017-03-03 06:03:03 Folder1",
            "dm       0 2017-03-03 06:03:02 1Folder with space",
        ]

    def test_column_formatter(self):
        formatter = VerticalColumnsFilesFormatter(width=40)
        assert list(formatter(self.files_and_folders)) == [
            "File1             Folder1",
            "File2             1Folder with space",
            "File3 with space",
        ]

        formatter = VerticalColumnsFilesFormatter(width=36)
        assert list(formatter(self.files_and_folders)) == [
            "File1             Folder1",
            "File2             1Folder with space",
            "File3 with space",
        ]

        formatter = VerticalColumnsFilesFormatter(width=1)
        assert list(formatter(self.files_and_folders)) == [
            "File1",
            "File2",
            "File3 with space",
            "Folder1",
            "1Folder with space",
        ]

    @pytest.mark.parametrize(
        "formatter",
        [
            (SimpleFilesFormatter()),
            (VerticalColumnsFilesFormatter(width=100)),
            (LongFilesFormatter(human_readable=False)),
        ],
    )
    def test_formatter_with_empty_files(self, formatter):
        files = []
        assert [] == list(formatter(files))

    def test_sorter(self):
        sorter = FilesSorter.NAME
        files = sorted(self.files_and_folders, key=sorter.key())
        assert files == [
            self.folders[1],
            self.files[0],
            self.files[1],
            self.files[2],
            self.folders[0],
        ]

        sorter = FilesSorter.SIZE
        files = sorted(self.files_and_folders, key=sorter.key())
        assert files[2:5] == [self.files[1], self.files[0], self.files[2]]

        sorter = FilesSorter.TIME
        files = sorted(self.files_and_folders, key=sorter.key())
        assert files == [
            self.folders[1],
            self.folders[0],
            self.files[0],
            self.files[1],
            self.files[2],
        ]


class TestResourcesFormatter:
    def test_tiny_container(self) -> None:
        resources = Resources.create(
            cpu=0.1, gpu=0, gpu_model=None, memory=16, extshm=False
        )
        resource_formatter = ResourcesFormatter()
        assert (
            resource_formatter(resources) == "Resources:\n"
            "  Memory: 16 MB\n"
            "  CPU: 0.1"
        )

    def test_gpu_container(self) -> None:
        resources = Resources.create(
            cpu=2, gpu=1, gpu_model="nvidia-tesla-p4", memory=1024, extshm=False
        )
        resource_formatter = ResourcesFormatter()
        assert (
            resource_formatter(resources) == "Resources:\n"
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
            resource_formatter(resources) == "Resources:\n"
            "  Memory: 16 MB\n"
            "  CPU: 0.1\n"
            "  Additional: Extended SHM space"
        )


class TestConfigFormatter:
    def test_output(self, token) -> None:
        config = Config(
            auth_token=AuthToken(
                token=token, refresh_token="refresh-token", expiration_time=123_456
            ),
            github_rsa_path="path",
        )
        out = ConfigFormatter()(config)
        assert out == textwrap.dedent(
            """\
            Config:
              User Name: user
              API URL: https://platform.dev.neuromation.io/api/v1
              Docker Registry URL: https://registry.dev.neuromation.io
              Github RSA Path: path"""
        )
