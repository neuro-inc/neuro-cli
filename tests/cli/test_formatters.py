import textwrap
import time
from dataclasses import replace
from datetime import datetime
from typing import Any, List, Optional

import click
import pytest
from yarl import URL

from neuromation.api import (
    Container,
    FileStatus,
    FileStatusType,
    HTTPPort,
    JobDescription,
    JobStatus,
    JobStatusHistory,
    JobTelemetry,
    RemoteImage,
    Resources,
)
from neuromation.api.parsing_utils import _ImageNameParser
from neuromation.cli.formatters import (
    BaseFilesFormatter,
    ConfigFormatter,
    DockerImageOperation,
    DockerImageProgress,
    JobFormatter,
    JobStartProgress,
    JobStatusFormatter,
    JobTelemetryFormatter,
    SimpleJobsFormatter,
    TabularJobsFormatter,
)
from neuromation.cli.formatters.jobs import ResourcesFormatter, TabularJobRow
from neuromation.cli.formatters.storage import (
    BSDAttributes,
    BSDPainter,
    FilesSorter,
    GnuIndicators,
    GnuPainter,
    LongFilesFormatter,
    NonePainter,
    QuotedPainter,
    SimpleFilesFormatter,
    VerticalColumnsFilesFormatter,
    get_painter,
)
from neuromation.cli.printer import CSI
from neuromation.cli.root import Root


TEST_JOB_ID = "job-ad09fe07-0c64-4d32-b477-3b737d215621"
TEST_JOB_NAME = "test-job-name"


@pytest.fixture
def job_descr_no_name() -> JobDescription:
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
            image=RemoteImage("ubuntu", "latest"),
            resources=Resources(16, 0.1, 0, None, False),
        ),
        ssh_auth_server=URL("ssh-auth"),
        is_preemptible=True,
    )


@pytest.fixture
def job_descr() -> JobDescription:
    return JobDescription(
        status=JobStatus.PENDING,
        id=TEST_JOB_ID,
        name=TEST_JOB_NAME,
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
            image=RemoteImage("ubuntu", "latest"),
            resources=Resources(16, 0.1, 0, None, False),
        ),
        ssh_auth_server=URL("ssh-auth"),
        is_preemptible=True,
    )


class TestJobFormatter:
    def test_quiet_no_name(self, job_descr_no_name: JobDescription) -> None:
        assert JobFormatter(quiet=True)(job_descr_no_name) == TEST_JOB_ID

    def test_quiet(self, job_descr: JobDescription) -> None:
        assert JobFormatter(quiet=True)(job_descr) == TEST_JOB_ID

    def test_non_quiet_no_name(self, job_descr_no_name: JobDescription) -> None:
        expected = (
            f"Job ID: {TEST_JOB_ID} Status: {JobStatus.PENDING}\n"
            + f"Shortcuts:\n"
            + f"  neuro status {TEST_JOB_ID}  # check job status\n"
            + f"  neuro logs {TEST_JOB_ID}    # monitor job stdout\n"
            + f"  neuro top {TEST_JOB_ID}     # display real-time job telemetry\n"
            + f"  neuro kill {TEST_JOB_ID}    # kill job"
        )
        assert click.unstyle(JobFormatter(quiet=False)(job_descr_no_name)) == expected

    def test_non_quiet(self, job_descr: JobDescription) -> None:
        expected = (
            f"Job ID: {TEST_JOB_ID} Status: {JobStatus.PENDING}\n"
            + f"Name: {TEST_JOB_NAME}\n"
            + f"Shortcuts:\n"
            + f"  neuro status {TEST_JOB_NAME}  # check job status\n"
            + f"  neuro logs {TEST_JOB_NAME}    # monitor job stdout\n"
            + f"  neuro top {TEST_JOB_NAME}     # display real-time job telemetry\n"
            + f"  neuro kill {TEST_JOB_NAME}    # kill job"
        )
        assert click.unstyle(JobFormatter(quiet=False)(job_descr)) == expected

    def test_non_quiet_http_url_no_name(
        self, job_descr_no_name: JobDescription
    ) -> None:
        job_descr_no_name = replace(job_descr_no_name, http_url=URL("https://job.dev"))
        expected = (
            f"Job ID: {TEST_JOB_ID} Status: {JobStatus.PENDING}\n"
            + f"Http URL: https://job.dev\n"
            + f"Shortcuts:\n"
            + f"  neuro status {TEST_JOB_ID}  # check job status\n"
            + f"  neuro logs {TEST_JOB_ID}    # monitor job stdout\n"
            + f"  neuro top {TEST_JOB_ID}     # display real-time job telemetry\n"
            + f"  neuro kill {TEST_JOB_ID}    # kill job"
        )
        assert click.unstyle(JobFormatter(quiet=False)(job_descr_no_name)) == expected

    def test_non_quiet_http_url(self, job_descr: JobDescription) -> None:
        job_descr = replace(job_descr, http_url=URL("https://job.dev"))
        expected = (
            f"Job ID: {TEST_JOB_ID} Status: {JobStatus.PENDING}\n"
            + f"Name: {TEST_JOB_NAME}\n"
            + f"Http URL: https://job.dev\n"
            + f"Shortcuts:\n"
            + f"  neuro status {TEST_JOB_NAME}  # check job status\n"
            + f"  neuro logs {TEST_JOB_NAME}    # monitor job stdout\n"
            + f"  neuro top {TEST_JOB_NAME}     # display real-time job telemetry\n"
            + f"  neuro kill {TEST_JOB_NAME}    # kill job"
        )
        assert click.unstyle(JobFormatter(quiet=False)(job_descr)) == expected

    def test_non_quiet_http_url_named(self, job_descr: JobDescription) -> None:
        job_descr = replace(job_descr, http_url_named=URL("https://job-named.dev"))
        expected = (
            f"Job ID: {TEST_JOB_ID} Status: {JobStatus.PENDING}\n"
            + f"Name: {TEST_JOB_NAME}\n"
            + f"Http URL: https://job-named.dev\n"
            + f"Shortcuts:\n"
            + f"  neuro status {TEST_JOB_NAME}  # check job status\n"
            + f"  neuro logs {TEST_JOB_NAME}    # monitor job stdout\n"
            + f"  neuro top {TEST_JOB_NAME}     # display real-time job telemetry\n"
            + f"  neuro kill {TEST_JOB_NAME}    # kill job"
        )
        assert click.unstyle(JobFormatter(quiet=False)(job_descr)) == expected


class TestJobStartProgress:
    def make_job(self, status: JobStatus, reason: str) -> JobDescription:
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
                image=RemoteImage("test-image"),
                resources=Resources(16, 0.1, 0, None, False),
            ),
            ssh_auth_server=URL("ssh-auth"),
            is_preemptible=False,
        )

    def strip(self, text: str) -> str:
        return click.unstyle(text).strip()

    def test_quiet(self, capfd: Any) -> None:
        progress = JobStartProgress.create(tty=True, color=True, quiet=True)
        progress(self.make_job(JobStatus.PENDING, ""))
        progress.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ""

    def test_no_tty(self, capfd: Any, click_tty_emulation: Any) -> None:
        progress = JobStartProgress.create(tty=False, color=True, quiet=False)
        progress(self.make_job(JobStatus.PENDING, ""))
        progress(self.make_job(JobStatus.PENDING, ""))
        progress(self.make_job(JobStatus.RUNNING, "reason"))
        progress.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert f"{JobStatus.PENDING}" in out
        assert f"{JobStatus.RUNNING}" in out
        assert "reason (ErrorDesc)" in out
        assert out.count(f"{JobStatus.PENDING}") == 1
        assert CSI not in out

    def test_tty(self, capfd: Any, click_tty_emulation: Any) -> None:
        progress = JobStartProgress.create(tty=True, color=True, quiet=False)
        progress(self.make_job(JobStatus.PENDING, ""))
        progress(self.make_job(JobStatus.PENDING, ""))
        progress(self.make_job(JobStatus.RUNNING, "reason"))
        progress.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert f"{JobStatus.PENDING}" in out
        assert f"{JobStatus.RUNNING}" in out
        assert "reason" in out
        assert "(ErrorDesc)" in out
        assert out.count(f"{JobStatus.PENDING}") != 1
        assert CSI in out


class TestJobOutputFormatter:
    def test_job_with_name(self) -> None:
        description = JobDescription(
            status=JobStatus.FAILED,
            owner="test-user",
            id="test-job",
            name="test-job-name",
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
                exit_code=123,
            ),
            container=Container(
                command="test-command",
                image=RemoteImage("test-image"),
                resources=Resources(16, 0.1, 0, None, False),
                http=HTTPPort(port=80, requires_auth=True),
            ),
            ssh_auth_server=URL("ssh-auth"),
            is_preemptible=False,
        )

        status = JobStatusFormatter()(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Name: test-job-name\n"
            "Owner: test-user\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource_formatter(description.container.resources)}\n"
            "Preemptible: False\n"
            "Http URL: http://local.host.test/\n"
            "Http authentication: True\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 123\n"
            "===Description===\n"
            "ErrorDesc\n================="
        )

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
                exit_code=321,
            ),
            container=Container(
                command="test-command",
                image=RemoteImage("test-image"),
                resources=Resources(16, 0.1, 0, None, False),
                http=HTTPPort(port=80, requires_auth=True),
            ),
            ssh_auth_server=URL("ssh-auth"),
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
            "Http authentication: True\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 321\n"
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
                reason="",
                description="",
                created_at="2018-09-25T12:28:21.298672+00:00",
                started_at="",
                finished_at="",
            ),
            container=Container(
                command="test-command",
                image=RemoteImage("test-image"),
                resources=Resources(16, 0.1, 0, None, False),
            ),
            ssh_auth_server=URL("ssh-auth"),
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
                description="",
                created_at="2018-09-25T12:28:21.298672+00:00",
                started_at="",
                finished_at="",
            ),
            container=Container(
                image=RemoteImage("test-image"),
                command="test-command",
                resources=Resources(16, 0.1, 0, None, False),
            ),
            ssh_auth_server=URL("ssh-auth"),
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
                description="",
                created_at="2018-09-25T12:28:21.298672+00:00",
                started_at="",
                finished_at="",
            ),
            container=Container(
                image=RemoteImage("test-image"),
                command="test-command",
                resources=Resources(16, 0.1, 0, None, False),
            ),
            ssh_auth_server=URL("ssh-auth"),
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

    def test_running_job(self) -> None:
        description = JobDescription(
            status=JobStatus.RUNNING,
            owner="test-user",
            id="test-job",
            description="test job description",
            history=JobStatusHistory(
                status=JobStatus.RUNNING,
                reason="ContainerRunning",
                description="",
                created_at="2018-09-25T12:28:21.298672+00:00",
                started_at="2018-09-25T12:28:24.759433+00:00",
                finished_at="",
            ),
            http_url=URL("http://local.host.test/"),
            ssh_server=URL("ssh://local.host.test:22/"),
            container=Container(
                command="test-command",
                image=RemoteImage("test-image"),
                resources=Resources(16, 0.1, 0, None, False),
            ),
            ssh_auth_server=URL("ssh-auth"),
            is_preemptible=False,
            internal_hostname="host.local",
        )

        status = JobStatusFormatter()(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Owner: test-user\n"
            "Description: test job description\n"
            "Status: running\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource_formatter(description.container.resources)}\n"
            "Preemptible: False\n"
            "Internal Hostname: host.local\n"
            "Http URL: http://local.host.test/\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:24.759433+00:00"
        )


class TestJobTelemetryFormatter:
    def _format(
        self, timestamp: str, cpu: str, mem: str, gpu: str, gpu_mem: str
    ) -> str:
        return "\t".join(
            [
                f"{timestamp:<24}",
                f"{cpu:<15}",
                f"{mem:<15}",
                f"{gpu:<15}",
                f"{gpu_mem:<15}",
            ]
        )

    def test_format_header_line(self) -> None:
        line = JobTelemetryFormatter().header()
        assert line == self._format(
            timestamp="TIMESTAMP",
            cpu="CPU",
            mem="MEMORY (MB)",
            gpu="GPU (%)",
            gpu_mem="GPU_MEMORY (MB)",
        )

    def test_format_telemetry_line_no_gpu(self) -> None:
        formatter = JobTelemetryFormatter()
        # NOTE: the timestamp_str encodes the local timezone
        timestamp = 1_517_248_466.238_723_6
        timestamp_str = formatter._format_timestamp(timestamp)
        telemetry = JobTelemetry(cpu=0.12345, memory=256.123, timestamp=timestamp)
        line = JobTelemetryFormatter()(telemetry)
        assert line == self._format(
            timestamp=timestamp_str, cpu="0.123", mem="256.123", gpu="0", gpu_mem="0"
        )

    def test_format_telemetry_line_with_gpu(self) -> None:
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


class TestSimpleJobsFormatter:
    def test_empty(self) -> None:
        formatter = SimpleJobsFormatter()
        result = [item for item in formatter([])]
        assert result == []

    def test_list(self) -> None:
        jobs = [
            JobDescription(
                status=JobStatus.PENDING,
                id="job-42687e7c-6c76-4857-a6a7-1166f8295391",
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
                    image=RemoteImage("ubuntu", "latest"),
                    resources=Resources(16, 0.1, 0, None, False),
                ),
                ssh_auth_server=URL("ssh-auth"),
                is_preemptible=True,
            ),
            JobDescription(
                status=JobStatus.PENDING,
                id="job-cf33bd55-9e3b-4df7-a894-9c148a908a66",
                name="this-job-has-a-name",
                owner="owner",
                history=JobStatusHistory(
                    status=JobStatus.FAILED,
                    reason="ErrorReason",
                    description="ErrorDesc",
                    created_at="2018-09-25T12:28:21.298672+00:00",
                    started_at="2018-09-25T12:28:59.759433+00:00",
                    finished_at="2018-09-25T12:28:59.759433+00:00",
                ),
                container=Container(
                    image=RemoteImage("ubuntu", "latest"),
                    resources=Resources(16, 0.1, 0, None, False),
                ),
                ssh_auth_server=URL("ssh-auth"),
                is_preemptible=True,
            ),
        ]
        formatter = SimpleJobsFormatter()
        result = [item for item in formatter(jobs)]
        assert result == [
            "job-42687e7c-6c76-4857-a6a7-1166f8295391",
            "job-cf33bd55-9e3b-4df7-a894-9c148a908a66",
        ]


class TestTabularJobRow:
    image_parser = _ImageNameParser("bob", URL("https://registry-test.neu.ro"))

    def _job_descr_with_status(
        self, status: JobStatus, image: str = "nginx:latest", name: Optional[str] = None
    ) -> JobDescription:
        remote_image = self.image_parser.parse_remote(image)
        return JobDescription(
            status=status,
            id="job-1f5ab792-e534-4bb4-be56-8af1ce722692",
            name=name,
            owner="owner",
            description="some",
            history=JobStatusHistory(
                status=status,
                reason="ErrorReason",
                description="ErrorDesc",
                created_at="2017-01-02T12:28:21.298672+00:00",
                started_at="2017-02-03T12:28:59.759433+00:00",
                finished_at="2017-03-04T12:28:59.759433+00:00",
            ),
            container=Container(
                image=remote_image,
                resources=Resources(16, 0.1, 0, None, False),
                command="ls",
            ),
            ssh_auth_server=URL("ssh-auth"),
            is_preemptible=True,
        )

    def test_with_job_name(self) -> None:
        row = TabularJobRow.from_job(
            self._job_descr_with_status(JobStatus.RUNNING, name="job-name")
        )
        assert row.name == "job-name"

    def test_without_job_name(self) -> None:
        row = TabularJobRow.from_job(
            self._job_descr_with_status(JobStatus.RUNNING, name=None)
        )
        assert row.name == ""

    @pytest.mark.parametrize(
        "status,date",
        [
            (JobStatus.PENDING, "Jan 02 2017"),
            (JobStatus.RUNNING, "Feb 03 2017"),
            (JobStatus.FAILED, "Mar 04 2017"),
            (JobStatus.SUCCEEDED, "Mar 04 2017"),
        ],
    )
    def test_status_date_relation(self, status: JobStatus, date: str) -> None:
        row = TabularJobRow.from_job(self._job_descr_with_status(status))
        assert row.status == f"{status}"
        assert row.when == date

    def test_image_from_registry_parsing(self) -> None:
        row = TabularJobRow.from_job(
            self._job_descr_with_status(
                JobStatus.PENDING, "registry-test.neu.ro/bob/swiss-box:red"
            )
        )
        assert row.image == "image://bob/swiss-box:red"
        assert row.name == ""


class TestTabularJobsFormatter:
    columns = ["ID", "NAME", "STATUS", "WHEN", "IMAGE", "DESCRIPTION", "COMMAND"]
    image_parser = _ImageNameParser("bob", URL("https://registry-test.neu.ro"))

    def test_empty(self) -> None:
        formatter = TabularJobsFormatter(0)
        result = [item for item in formatter([])]
        assert result == ["  ".join(self.columns)]

    def test_width_cutting(self) -> None:
        formatter = TabularJobsFormatter(10)
        result = [item for item in formatter([])]
        assert result == ["  ".join(self.columns)[:10]]

    def test_short_cells(self) -> None:
        job = JobDescription(
            status=JobStatus.FAILED,
            id="j",
            owner="owner",
            name="name",
            description="d",
            history=JobStatusHistory(
                status=JobStatus.FAILED,
                reason="ErrorReason",
                description="ErrorDesc",
                created_at="2018-09-25T12:28:21.298672+00:00",
                started_at="2018-09-25T12:28:59.759433+00:00",
                finished_at=datetime.fromtimestamp(time.time() - 1).isoformat(),
            ),
            container=Container(
                image=RemoteImage("i", "l"),
                resources=Resources(16, 0.1, 0, None, False),
                command="c",
            ),
            ssh_auth_server=URL("ssh-auth"),
            is_preemptible=True,
        )
        formatter = TabularJobsFormatter(0)
        result = [item for item in formatter([job])]
        assert result in [
            [
                "ID  NAME  STATUS  WHEN  IMAGE  DESCRIPTION  COMMAND",
                "j   name  failed  now   i:l    d            c",
            ],
            [
                "ID  NAME  STATUS  WHEN          IMAGE  DESCRIPTION  COMMAND",
                "j   name  failed  a second ago  i:l    d            c",
            ],
            [
                "ID  NAME  STATUS  WHEN           IMAGE  DESCRIPTION  COMMAND",
                "j   name  failed  2 seconds ago  i:l    d            c",
            ],
        ]

    def test_wide_cells(self) -> None:
        jobs = [
            JobDescription(
                status=JobStatus.FAILED,
                id="job-7ee153a7-249c-4be9-965a-ba3eafb67c82",
                name="name1",
                owner="owner",
                description="some description long long long long",
                history=JobStatusHistory(
                    status=JobStatus.FAILED,
                    reason="ErrorReason",
                    description="ErrorDesc",
                    created_at="2018-09-25T12:28:21.298672+00:00",
                    started_at="2018-09-25T12:28:59.759433+00:00",
                    finished_at="2017-09-25T12:28:59.759433+00:00",
                ),
                container=Container(
                    image=RemoteImage("some-image-name", "with-long-tag"),
                    resources=Resources(16, 0.1, 0, None, False),
                    command="ls -la /some/path",
                ),
                ssh_auth_server=URL("ssh-auth"),
                is_preemptible=True,
            ),
            JobDescription(
                status=JobStatus.PENDING,
                id="job-7ee153a7-249c-4be9-965a-ba3eafb67c84",
                name="name2",
                owner="owner",
                description="some description",
                history=JobStatusHistory(
                    status=JobStatus.PENDING,
                    reason="",
                    description="",
                    created_at="2017-09-25T12:28:21.298672+00:00",
                    started_at="2018-09-25T12:28:59.759433+00:00",
                    finished_at="2017-09-25T12:28:59.759433+00:00",
                ),
                container=Container(
                    image=RemoteImage("some-image-name", "with-long-tag"),
                    resources=Resources(16, 0.1, 0, None, False),
                    command="ls -la /some/path",
                ),
                ssh_auth_server=URL("ssh-auth"),
                is_preemptible=True,
            ),
        ]
        formatter = TabularJobsFormatter(0)
        result = [item for item in formatter(jobs)]
        assert result == [
            "ID                                        NAME   STATUS   WHEN         IMAGE            DESCRIPTION                           COMMAND",  # noqa: E501
            "job-7ee153a7-249c-4be9-965a-ba3eafb67c82  name1  failed   Sep 25 2017  some-image-name:with-long-tag  some description long long long long  ls -la /some/path",  # noqa: E501
            "job-7ee153a7-249c-4be9-965a-ba3eafb67c84  name2  pending  Sep 25 2017  some-image-name:with-long-tag  some description        ls -la /some/path",  # noqa: E501
        ]


class TestNonePainter:
    def test_simple(self) -> None:
        painter = NonePainter()
        file = FileStatus(
            "File1",
            2048,
            FileStatusType.FILE,
            int(time.mktime(time.strptime("2018-01-01 03:00:00", "%Y-%m-%d %H:%M:%S"))),
            "read",
        )
        assert painter.paint(file.name, file.type) == file.name


class TestQuotedPainter:
    def test_simple(self) -> None:
        painter = QuotedPainter()
        file = FileStatus(
            "File1",
            2048,
            FileStatusType.FILE,
            int(time.mktime(time.strptime("2018-01-01 03:00:00", "%Y-%m-%d %H:%M:%S"))),
            "read",
        )
        assert painter.paint(file.name, file.type) == "'File1'"

    def test_has_quote(self) -> None:
        painter = QuotedPainter()
        file = FileStatus(
            "File1'2",
            2048,
            FileStatusType.FILE,
            int(time.mktime(time.strptime("2018-01-01 03:00:00", "%Y-%m-%d %H:%M:%S"))),
            "read",
        )
        assert painter.paint(file.name, file.type) == '''"File1'2"'''


class TestGnuPainter:
    def test_color_parsing_simple(self) -> None:
        painter = GnuPainter("rs=1;0;1")
        assert painter.color_indicator[GnuIndicators.RESET] == "1;0;1"

        painter = GnuPainter(":rs=1;0;1")
        assert painter.color_indicator[GnuIndicators.RESET] == "1;0;1"

        painter = GnuPainter("rs=1;0;1:")
        assert painter.color_indicator[GnuIndicators.RESET] == "1;0;1"

        painter = GnuPainter("rs=1;0;1:fi=32;42")
        assert painter.color_indicator[GnuIndicators.RESET] == "1;0;1"
        assert painter.color_indicator[GnuIndicators.FILE] == "32;42"

        painter = GnuPainter("rs=1;0;1:fi")
        assert painter.color_indicator[GnuIndicators.RESET] == "1;0;1"
        assert painter.color_indicator[GnuIndicators.FILE] == ""

        painter = GnuPainter("rs=1;0;1:fi=")
        assert painter.color_indicator[GnuIndicators.RESET] == "1;0;1"
        assert painter.color_indicator[GnuIndicators.FILE] == ""

    @pytest.mark.parametrize(
        "escaped,result",
        [
            ("\\a", "\a"),
            ("\\b", "\b"),
            ("\\e", chr(27)),
            ("\\f", "\f"),
            ("\\n", "\n"),
            ("\\r", "\r"),
            ("\\t", "\t"),
            ("\\v", "\v"),
            ("\\?", chr(127)),
            ("\\_", " "),
            ("a\\n", "a\n"),
            ("a\\tb", "a\tb"),
            ("a\\t\\rb", "a\t\rb"),
            ("a\\=b", "a=b"),
        ],
    )
    def test_color_parsing_escaped_simple(self, escaped: str, result: str) -> None:
        painter = GnuPainter("rs=" + escaped)
        assert painter.color_indicator[GnuIndicators.RESET] == result

        painter = GnuPainter(escaped + "=1;2")
        assert painter.color_ext_type[result] == "1;2"

        painter = GnuPainter(escaped + "=" + escaped)
        assert painter.color_ext_type[result] == result

    @pytest.mark.parametrize(
        "escaped,result",
        [
            ("\\7", chr(7)),
            ("\\8", "8"),
            ("\\10", chr(8)),
            ("a\\2", "a" + chr(2)),
            ("a\\2b", "a" + chr(2) + "b"),
        ],
    )
    def test_color_parsing_escaped_octal(self, escaped: str, result: str) -> None:
        painter = GnuPainter("rs=" + escaped)
        assert painter.color_indicator[GnuIndicators.RESET] == result

        painter = GnuPainter(escaped + "=1;2")
        assert painter.color_ext_type[result] == "1;2"

        painter = GnuPainter(escaped + "=" + escaped)
        assert painter.color_ext_type[result] == result

    @pytest.mark.parametrize(
        "escaped,result",
        [
            ("\\x7", chr(0x7)),
            ("\\x8", chr(0x8)),
            ("\\x10", chr(0x10)),
            ("\\XaA", chr(0xAA)),
            ("a\\x222", "a" + chr(0x22) + "2"),
            ("a\\x2z", "a" + chr(0x2) + "z"),
        ],
    )
    def test_color_parsing_escaped_hex(self, escaped: str, result: str) -> None:
        painter = GnuPainter("rs=" + escaped)
        assert painter.color_indicator[GnuIndicators.RESET] == result

        painter = GnuPainter(escaped + "=1;2")
        assert painter.color_ext_type[result] == "1;2"

        painter = GnuPainter(escaped + "=" + escaped)
        assert painter.color_ext_type[result] == result

    @pytest.mark.parametrize(
        "escaped,result",
        [
            ("^a", chr(1)),
            ("^?", chr(127)),
            ("^z", chr(26)),
            ("a^Z", "a" + chr(26)),
            ("a^Zb", "a" + chr(26) + "b"),
        ],
    )
    def test_color_parsing_carret(self, escaped: str, result: str) -> None:
        painter = GnuPainter("rs=" + escaped)
        assert painter.color_indicator[GnuIndicators.RESET] == result

        painter = GnuPainter(escaped + "=1;2")
        assert painter.color_ext_type[result] == "1;2"

        painter = GnuPainter(escaped + "=" + escaped)
        assert painter.color_ext_type[result] == result

    @pytest.mark.parametrize("escaped", [("^1"), ("^"), ("^" + chr(130))])
    def test_color_parsing_carret_incorrect(self, escaped: str) -> None:
        with pytest.raises(EnvironmentError):
            GnuPainter("rs=" + escaped)

        with pytest.raises(EnvironmentError):
            GnuPainter(escaped + "=1;2")

    def test_coloring(self) -> None:
        file = FileStatus(
            "test.txt",
            1024,
            FileStatusType.FILE,
            int(time.mktime(time.strptime("2018-01-01 03:00:00", "%Y-%m-%d %H:%M:%S"))),
            "read",
        )
        folder = FileStatus(
            "tmp",
            0,
            FileStatusType.DIRECTORY,
            int(time.mktime(time.strptime("2018-01-01 03:00:00", "%Y-%m-%d %H:%M:%S"))),
            "write",
        )
        painter = GnuPainter("di=32;41:fi=0;44:no=0;46")
        assert painter.paint(file.name, file.type) == "\x1b[0;44mtest.txt\x1b[0m"
        assert painter.paint(folder.name, folder.type) == "\x1b[32;41mtmp\x1b[0m"

        painter = GnuPainter("di=32;41:no=0;46")
        assert painter.paint(file.name, file.type) == "\x1b[0;46mtest.txt\x1b[0m"
        assert painter.paint(folder.name, folder.type) == "\x1b[32;41mtmp\x1b[0m"

        painter = GnuPainter("no=0;46")
        assert painter.paint(file.name, file.type) == "\x1b[0;46mtest.txt\x1b[0m"
        assert painter.paint(folder.name, folder.type) == "\x1b[01;34mtmp\x1b[0m"

        painter = GnuPainter("*.text=0;46")
        assert painter.paint(file.name, file.type) == "test.txt"
        assert painter.paint(folder.name, folder.type) == "\x1b[01;34mtmp\x1b[0m"

        painter = GnuPainter("*.txt=0;46")
        assert painter.paint(file.name, file.type) == "\x1b[0;46mtest.txt\x1b[0m"
        assert painter.paint(folder.name, folder.type) == "\x1b[01;34mtmp\x1b[0m"


class TestBSDPainter:
    def test_color_parsing(self) -> None:
        painter = BSDPainter("exfxcxdxbxegedabagacad")
        assert painter._colors[BSDAttributes.DIRECTORY] == "ex"

    def test_coloring(self) -> None:
        file = FileStatus(
            "test.txt",
            1024,
            FileStatusType.FILE,
            int(time.mktime(time.strptime("2018-01-01 03:00:00", "%Y-%m-%d %H:%M:%S"))),
            "read",
        )
        folder = FileStatus(
            "tmp",
            0,
            FileStatusType.DIRECTORY,
            int(time.mktime(time.strptime("2018-01-01 03:00:00", "%Y-%m-%d %H:%M:%S"))),
            "write",
        )
        painter = BSDPainter("exfxcxdxbxegedabagacad")
        assert painter.paint(file.name, file.type) == "test.txt"
        assert painter.paint(folder.name, folder.type) == click.style("tmp", fg="blue")

        painter = BSDPainter("Eafxcxdxbxegedabagacad")
        assert painter.paint(file.name, file.type) == "test.txt"
        assert painter.paint(folder.name, folder.type) == click.style(
            "tmp", fg="blue", bg="black", bold=True
        )


class TestPainterFactory:
    def test_detection(self, monkeypatch: Any) -> None:
        monkeypatch.setenv("LS_COLORS", "")
        monkeypatch.setenv("LSCOLORS", "")
        painter = get_painter(True)
        assert isinstance(painter, NonePainter)

        monkeypatch.setenv("LSCOLORS", "exfxcxdxbxegedabagacad")
        monkeypatch.setenv("LS_COLORS", "di=32;41:fi=0;44:no=0;46")
        painter_without_color = get_painter(False)
        painter_with_color = get_painter(True)
        assert isinstance(painter_without_color, NonePainter)
        assert not isinstance(painter_with_color, NonePainter)

        monkeypatch.setenv("LSCOLORS", "")
        monkeypatch.setenv("LS_COLORS", "di=32;41:fi=0;44:no=0;46")
        painter = get_painter(True)
        assert isinstance(painter, GnuPainter)

        monkeypatch.setenv("LSCOLORS", "exfxcxdxbxegedabagacad")
        monkeypatch.setenv("LS_COLORS", "")
        painter = get_painter(True)
        assert isinstance(painter, BSDPainter)


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

    def test_simple_formatter(self) -> None:
        formatter = SimpleFilesFormatter(color=False)
        assert list(formatter(self.files_and_folders)) == [
            f"{file.name}" for file in self.files_and_folders
        ]

    def test_long_formatter(self) -> None:
        formatter = LongFilesFormatter(human_readable=False, color=False)
        assert list(formatter(self.files_and_folders)) == [
            "-r    2048 2018-01-01 03:00:00 File1",
            "-r    1024 2018-10-10 13:10:10 File2",
            "-r 1024001 2019-02-02 05:02:02 File3 with space",
            "dm       0 2017-03-03 06:03:03 Folder1",
            "dm       0 2017-03-03 06:03:02 1Folder with space",
        ]

        formatter = LongFilesFormatter(human_readable=True, color=False)
        assert list(formatter(self.files_and_folders)) == [
            "-r    2.0K 2018-01-01 03:00:00 File1",
            "-r    1.0K 2018-10-10 13:10:10 File2",
            "-r 1000.0K 2019-02-02 05:02:02 File3 with space",
            "dm       0 2017-03-03 06:03:03 Folder1",
            "dm       0 2017-03-03 06:03:02 1Folder with space",
        ]

    def test_column_formatter(self) -> None:
        formatter = VerticalColumnsFilesFormatter(width=40, color=False)
        assert list(formatter(self.files_and_folders)) == [
            "File1             Folder1",
            "File2             1Folder with space",
            "File3 with space",
        ]

        formatter = VerticalColumnsFilesFormatter(width=36, color=False)
        assert list(formatter(self.files_and_folders)) == [
            "File1             Folder1",
            "File2             1Folder with space",
            "File3 with space",
        ]

        formatter = VerticalColumnsFilesFormatter(width=1, color=False)
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
            (SimpleFilesFormatter(color=False)),
            (VerticalColumnsFilesFormatter(width=100, color=False)),
            (LongFilesFormatter(human_readable=False, color=False)),
        ],
    )
    def test_formatter_with_empty_files(self, formatter: BaseFilesFormatter) -> None:
        files: List[FileStatus] = []
        assert [] == list(formatter(files))

    def test_sorter(self) -> None:
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
        resources = Resources(cpu=0.1, gpu=0, gpu_model=None, memory_mb=16, shm=False)
        resource_formatter = ResourcesFormatter()
        assert (
            resource_formatter(resources) == "Resources:\n"
            "  Memory: 16 MB\n"
            "  CPU: 0.1"
        )

    def test_gpu_container(self) -> None:
        resources = Resources(
            cpu=2, gpu=1, gpu_model="nvidia-tesla-p4", memory_mb=1024, shm=False
        )
        resource_formatter = ResourcesFormatter()
        assert (
            resource_formatter(resources) == "Resources:\n"
            "  Memory: 1024 MB\n"
            "  CPU: 2.0\n"
            "  GPU: 1.0 x nvidia-tesla-p4"
        )

    def test_shm_container(self) -> None:
        resources = Resources(cpu=0.1, gpu=0, gpu_model=None, memory_mb=16, shm=True)
        resource_formatter = ResourcesFormatter()
        assert (
            resource_formatter(resources) == "Resources:\n"
            "  Memory: 16 MB\n"
            "  CPU: 0.1\n"
            "  Additional: Extended SHM space"
        )


class TestConfigFormatter:
    async def test_output(self, root: Root) -> None:
        out = ConfigFormatter()(root)
        assert click.unstyle(out) == textwrap.dedent(
            """\
            User Configuration:
              User Name: user
              API URL: https://dev.neu.ro/api/v1
              Docker Registry URL: https://registry-dev.neu.ro
              Resource Presets:
                Name         #CPU  Memory #GPU  GPU Model
                gpu-small       7   30720    1  nvidia-tesla-k80
                gpu-large       7   61440    1  nvidia-tesla-v100
                cpu-small       7    2048
                cpu-large       7   14336"""
        )


class TestDockerImageProgress:
    def test_quiet(self, capfd: Any) -> None:
        formatter = DockerImageProgress.create(
            DockerImageOperation.PULL, tty=True, quiet=True
        )
        formatter.start("input", "output")
        formatter.progress("message1", "layer1")
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ""

    def test_no_tty(self, capfd: Any, click_tty_emulation: Any) -> None:
        formatter = DockerImageProgress.create(
            DockerImageOperation.PUSH, tty=False, quiet=False
        )
        formatter.start("input:latest", "image://bob/output:stream")
        formatter.progress("message1", "layer1")
        formatter.progress("message2", "layer1")

        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert "input:latest" in out
        assert "image://bob/output:stream" in out
        assert "message1" not in out
        assert "message2" not in out
        assert CSI not in out

    def test_tty(self, capfd: Any, click_tty_emulation: Any) -> None:
        formatter = DockerImageProgress.create(
            DockerImageOperation.PUSH, tty=True, quiet=False
        )
        formatter.start("input:latest", "image://bob/output:stream")
        formatter.progress("message1", "layer1")
        formatter.progress("message2", "layer1")
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert "input:latest" in out
        assert "image://bob/output:stream" in out
        assert "message1" in out
        assert "message2" in out
        assert CSI in out
