import textwrap
import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from sys import platform
from typing import Any, Callable, List, Optional

import click
import pytest
from dateutil.parser import isoparse
from yarl import URL

from neuromation.api import (
    Action,
    Client,
    Cluster,
    Container,
    FileStatus,
    FileStatusType,
    HTTPPort,
    ImageProgressPull,
    ImageProgressPush,
    ImageProgressStep,
    JobDescription,
    JobStatus,
    JobStatusHistory,
    JobTelemetry,
    LocalImage,
    Preset,
    RemoteImage,
    Resources,
    Volume,
)
from neuromation.api.abc import (
    ImageCommitFinished,
    ImageCommitStarted,
    ImageProgressSave,
)
from neuromation.api.admin import (
    _CloudProvider,
    _Cluster,
    _ClusterUser,
    _ClusterUserRoleType,
    _NodePool,
    _Quota,
    _Storage,
)
from neuromation.api.parsing_utils import _ImageNameParser
from neuromation.api.quota import _QuotaInfo
from neuromation.cli.formatters import (
    BaseFilesFormatter,
    ClustersFormatter,
    ClusterUserFormatter,
    ConfigFormatter,
    DockerImageProgress,
    JobFormatter,
    JobStartProgress,
    JobStatusFormatter,
    JobTelemetryFormatter,
    SimpleJobsFormatter,
    TabularJobsFormatter,
)
from neuromation.cli.formatters.config import QuotaFormatter, QuotaInfoFormatter
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
from neuromation.cli.parse_utils import parse_columns
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
        cluster_name="default",
        history=JobStatusHistory(
            status=JobStatus.PENDING,
            reason="ErrorReason",
            description="ErrorDesc",
            created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
            started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
            finished_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
        ),
        container=Container(
            image=RemoteImage("ubuntu", "latest"),
            resources=Resources(16, 0.1, 0, None, False, None, None),
        ),
        ssh_server=URL("ssh-auth"),
        is_preemptible=True,
    )


@pytest.fixture
def job_descr() -> JobDescription:
    return JobDescription(
        status=JobStatus.PENDING,
        id=TEST_JOB_ID,
        name=TEST_JOB_NAME,
        owner="owner",
        cluster_name="default",
        history=JobStatusHistory(
            status=JobStatus.PENDING,
            reason="ErrorReason",
            description="ErrorDesc",
            created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
            started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
            finished_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
        ),
        container=Container(
            image=RemoteImage("ubuntu", "latest"),
            resources=Resources(16, 0.1, 0, None, False, None, None),
        ),
        ssh_server=URL("ssh-auth"),
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
            f"Shortcuts:\n"
            f"  neuro status {TEST_JOB_ID}     # check job status\n"
            f"  neuro logs {TEST_JOB_ID}       # monitor job stdout\n"
            f"  neuro top {TEST_JOB_ID}        # display real-time job telemetry\n"
            f"  neuro exec {TEST_JOB_ID} bash  # execute bash shell to the job\n"
            f"  neuro kill {TEST_JOB_ID}       # kill job"
        )
        assert click.unstyle(JobFormatter(quiet=False)(job_descr_no_name)) == expected

    def test_non_quiet(self, job_descr: JobDescription) -> None:
        expected = (
            f"Job ID: {TEST_JOB_ID} Status: {JobStatus.PENDING}\n"
            f"Name: {TEST_JOB_NAME}\n"
            f"Shortcuts:\n"
            f"  neuro status {TEST_JOB_NAME}     # check job status\n"
            f"  neuro logs {TEST_JOB_NAME}       # monitor job stdout\n"
            f"  neuro top {TEST_JOB_NAME}        # display real-time job telemetry\n"
            f"  neuro exec {TEST_JOB_NAME} bash  # execute bash shell to the job\n"
            f"  neuro kill {TEST_JOB_NAME}       # kill job"
        )
        assert click.unstyle(JobFormatter(quiet=False)(job_descr)) == expected

    def test_non_quiet_http_url_no_name(
        self, job_descr_no_name: JobDescription
    ) -> None:
        job_descr_no_name = replace(job_descr_no_name, http_url=URL("https://job.dev"))
        expected = (
            f"Job ID: {TEST_JOB_ID} Status: {JobStatus.PENDING}\n"
            f"Http URL: https://job.dev\n"
            f"Shortcuts:\n"
            f"  neuro status {TEST_JOB_ID}     # check job status\n"
            f"  neuro logs {TEST_JOB_ID}       # monitor job stdout\n"
            f"  neuro top {TEST_JOB_ID}        # display real-time job telemetry\n"
            f"  neuro exec {TEST_JOB_ID} bash  # execute bash shell to the job\n"
            f"  neuro kill {TEST_JOB_ID}       # kill job"
        )
        assert click.unstyle(JobFormatter(quiet=False)(job_descr_no_name)) == expected

    def test_non_quiet_http_url(self, job_descr: JobDescription) -> None:
        job_descr = replace(job_descr, http_url=URL("https://job.dev"))
        expected = (
            f"Job ID: {TEST_JOB_ID} Status: {JobStatus.PENDING}\n"
            f"Name: {TEST_JOB_NAME}\n"
            f"Http URL: https://job.dev\n"
            f"Shortcuts:\n"
            f"  neuro status {TEST_JOB_NAME}     # check job status\n"
            f"  neuro logs {TEST_JOB_NAME}       # monitor job stdout\n"
            f"  neuro top {TEST_JOB_NAME}        # display real-time job telemetry\n"
            f"  neuro exec {TEST_JOB_NAME} bash  # execute bash shell to the job\n"
            f"  neuro kill {TEST_JOB_NAME}       # kill job"
        )
        assert click.unstyle(JobFormatter(quiet=False)(job_descr)) == expected

    def test_non_quiet_http_url_named(self, job_descr: JobDescription) -> None:
        job_descr = replace(job_descr, http_url=URL("https://job-named.dev"))
        expected = (
            f"Job ID: {TEST_JOB_ID} Status: {JobStatus.PENDING}\n"
            f"Name: {TEST_JOB_NAME}\n"
            f"Http URL: https://job-named.dev\n"
            f"Shortcuts:\n"
            f"  neuro status {TEST_JOB_NAME}     # check job status\n"
            f"  neuro logs {TEST_JOB_NAME}       # monitor job stdout\n"
            f"  neuro top {TEST_JOB_NAME}        # display real-time job telemetry\n"
            f"  neuro exec {TEST_JOB_NAME} bash  # execute bash shell to the job\n"
            f"  neuro kill {TEST_JOB_NAME}       # kill job"
        )
        assert click.unstyle(JobFormatter(quiet=False)(job_descr)) == expected


class TestJobStartProgress:
    def make_job(self, status: JobStatus, reason: str) -> JobDescription:
        return JobDescription(
            status=status,
            owner="test-user",
            cluster_name="default",
            id="test-job",
            description="test job description",
            http_url=URL("http://local.host.test/"),
            history=JobStatusHistory(
                status=status,
                reason=reason,
                description="ErrorDesc",
                created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                finished_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
            ),
            container=Container(
                command="test-command",
                image=RemoteImage("test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
            ),
            ssh_server=URL("ssh-auth"),
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
            cluster_name="default",
            id="test-job",
            name="test-job-name",
            description="test job description",
            http_url=URL("http://local.host.test/"),
            history=JobStatusHistory(
                status=JobStatus.PENDING,
                reason="ErrorReason",
                description="ErrorDesc",
                created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                finished_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                exit_code=123,
            ),
            container=Container(
                command="test-command",
                image=RemoteImage("test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
                http=HTTPPort(port=80, requires_auth=True),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
        )

        status = JobStatusFormatter()(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Name: test-job-name\n"
            "Owner: test-user\n"
            "Cluster: default\n"
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
            cluster_name="default",
            id="test-job",
            description="test job description",
            http_url=URL("http://local.host.test/"),
            history=JobStatusHistory(
                status=JobStatus.PENDING,
                reason="ErrorReason",
                description="ErrorDesc",
                created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                finished_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                exit_code=321,
            ),
            container=Container(
                command="test-command",
                image=RemoteImage("test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
                http=HTTPPort(port=80, requires_auth=True),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
        )

        status = JobStatusFormatter()(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Owner: test-user\n"
            "Cluster: default\n"
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
                created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                started_at=None,
                finished_at=None,
            ),
            container=Container(
                command="test-command",
                image=RemoteImage("test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=True,
            owner="owner",
            cluster_name="default",
        )

        status = JobStatusFormatter()(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Owner: owner\n"
            "Cluster: default\n"
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
                created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                started_at=None,
                finished_at=None,
            ),
            container=Container(
                image=RemoteImage("test-image"),
                command="test-command",
                resources=Resources(16, 0.1, 0, None, False, None, None),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=True,
            owner="owner",
            cluster_name="default",
        )

        status = JobStatusFormatter()(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Owner: owner\n"
            "Cluster: default\n"
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
                created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                started_at=None,
                finished_at=None,
            ),
            container=Container(
                image=RemoteImage("test-image"),
                command="test-command",
                resources=Resources(16, 0.1, 0, None, False, None, None),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=True,
            owner="owner",
            cluster_name="default",
        )

        status = JobStatusFormatter()(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Owner: owner\n"
            "Cluster: default\n"
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
            cluster_name="default",
            id="test-job",
            description="test job description",
            history=JobStatusHistory(
                status=JobStatus.RUNNING,
                reason="ContainerRunning",
                description="",
                created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                started_at=isoparse("2018-09-25T12:28:24.759433+00:00"),
                finished_at=None,
            ),
            http_url=URL("http://local.host.test/"),
            container=Container(
                command="test-command",
                image=RemoteImage("test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
            internal_hostname="host.local",
        )

        status = JobStatusFormatter()(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Owner: test-user\n"
            "Cluster: default\n"
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

    def test_job_with_entrypoint(self) -> None:
        description = JobDescription(
            status=JobStatus.RUNNING,
            owner="test-user",
            cluster_name="default",
            id="test-job",
            description="test job description",
            history=JobStatusHistory(
                status=JobStatus.RUNNING,
                reason="ContainerRunning",
                description="",
                created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                started_at=isoparse("2018-09-25T12:28:24.759433+00:00"),
                finished_at=None,
            ),
            http_url=URL("http://local.host.test/"),
            container=Container(
                entrypoint="/usr/bin/make",
                command="test",
                image=RemoteImage("test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
            internal_hostname="host.local",
        )

        status = JobStatusFormatter()(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: running\n"
            "Image: test-image\n"
            "Entrypoint: /usr/bin/make\n"
            "Command: test\n"
            f"{resource_formatter(description.container.resources)}\n"
            "Preemptible: False\n"
            "Internal Hostname: host.local\n"
            "Http URL: http://local.host.test/\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:24.759433+00:00"
        )

    def test_job_with_volumes(self) -> None:
        description = JobDescription(
            status=JobStatus.FAILED,
            owner="test-user",
            cluster_name="default",
            id="test-job",
            name="test-job-name",
            description="test job description",
            http_url=URL("http://local.host.test/"),
            history=JobStatusHistory(
                status=JobStatus.PENDING,
                reason="ErrorReason",
                description="ErrorDesc",
                created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                finished_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                exit_code=123,
            ),
            container=Container(
                command="test-command",
                image=RemoteImage("test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
                http=HTTPPort(port=80, requires_auth=True),
                volumes=[
                    Volume(
                        storage_uri=URL("storage://test-user/ro"),
                        container_path="/mnt/ro",
                        read_only=True,
                    ),
                    Volume(
                        storage_uri=URL("storage://test-user/rw"),
                        container_path="/mnt/rw",
                        read_only=False,
                    ),
                ],
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
        )

        status = JobStatusFormatter()(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Name: test-job-name\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource_formatter(description.container.resources)}\n"
            "Preemptible: False\n"
            "Volumes:\n"
            "  /mnt/ro  storage://test-user/ro  READONLY\n"
            "  /mnt/rw  storage://test-user/rw          \n"
            "Http URL: http://local.host.test/\n"
            "Http authentication: True\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 123\n"
            "===Description===\n"
            "ErrorDesc\n================="
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
                cluster_name="default",
                history=JobStatusHistory(
                    status=JobStatus.PENDING,
                    reason="ErrorReason",
                    description="ErrorDesc",
                    created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                    started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                    finished_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                ),
                container=Container(
                    image=RemoteImage("ubuntu", "latest"),
                    resources=Resources(16, 0.1, 0, None, False, None, None),
                ),
                ssh_server=URL("ssh-auth"),
                is_preemptible=True,
            ),
            JobDescription(
                status=JobStatus.PENDING,
                id="job-cf33bd55-9e3b-4df7-a894-9c148a908a66",
                name="this-job-has-a-name",
                owner="owner",
                cluster_name="default",
                history=JobStatusHistory(
                    status=JobStatus.FAILED,
                    reason="ErrorReason",
                    description="ErrorDesc",
                    created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                    started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                    finished_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                ),
                container=Container(
                    image=RemoteImage("ubuntu", "latest"),
                    resources=Resources(16, 0.1, 0, None, False, None, None),
                ),
                ssh_server=URL("ssh-auth"),
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
            cluster_name="default",
            description="some",
            history=JobStatusHistory(
                status=status,
                reason="ErrorReason",
                description="ErrorDesc",
                created_at=isoparse("2017-01-02T12:28:21.298672+00:00"),
                started_at=isoparse("2017-02-03T12:28:59.759433+00:00"),
                finished_at=isoparse("2017-03-04T12:28:59.759433+00:00"),
            ),
            container=Container(
                image=remote_image,
                resources=Resources(16, 0.1, 0, None, False, None, None),
                command="ls",
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=True,
        )

    def test_with_job_name(self) -> None:
        row = TabularJobRow.from_job(
            self._job_descr_with_status(JobStatus.RUNNING, name="job-name"), "owner"
        )
        assert row.name == "job-name"

    def test_without_job_name(self) -> None:
        row = TabularJobRow.from_job(
            self._job_descr_with_status(JobStatus.RUNNING, name=None), "owner"
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
        row = TabularJobRow.from_job(self._job_descr_with_status(status), "owner")
        assert row.status == f"{status}"
        assert row.when == date

    def test_image_from_registry_parsing(self) -> None:
        row = TabularJobRow.from_job(
            self._job_descr_with_status(
                JobStatus.PENDING, "registry-test.neu.ro/bob/swiss-box:red"
            ),
            "owner",
        )
        assert row.image == "image://bob/swiss-box:red"
        assert row.name == ""


class TestTabularJobsFormatter:
    columns = [
        "ID",
        "NAME",
        "STATUS",
        "WHEN",
        "IMAGE",
        "OWNER",
        "CLUSTER",
        "DESCRIPTION",
        "COMMAND",
    ]
    image_parser = _ImageNameParser("bob", URL("https://registry-test.neu.ro"))

    def test_empty(self) -> None:
        formatter = TabularJobsFormatter(0, "owner", parse_columns(None))
        result = [item for item in formatter([])]
        assert result == ["  ".join(self.columns)]

    def test_width_cutting(self) -> None:
        formatter = TabularJobsFormatter(10, "owner", parse_columns(None))
        result = [item for item in formatter([])]
        assert result == ["  ".join(self.columns)[:10]]

    @pytest.mark.parametrize(
        "owner_name,owner_printed", [("owner", "<you>"), ("alice", "alice")]
    )
    def test_short_cells(self, owner_name: str, owner_printed: str) -> None:
        job = JobDescription(
            status=JobStatus.FAILED,
            id="j",
            owner=owner_name,
            cluster_name="dc",
            name="name",
            description="d",
            history=JobStatusHistory(
                status=JobStatus.FAILED,
                reason="ErrorReason",
                description="ErrorDesc",
                created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                finished_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            ),
            container=Container(
                image=RemoteImage("i", "l"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
                command="c",
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=True,
        )
        formatter = TabularJobsFormatter(0, "owner", parse_columns(None))
        result = [item.rstrip() for item in formatter([job])]
        assert result in [
            [
                "ID  NAME  STATUS  WHEN  IMAGE  OWNER  CLUSTER  DESCRIPTION  COMMAND",
                f"j   name  failed  now   i:l    {owner_printed}  dc       d            c",  # noqa: E501
            ],
            [
                "ID  NAME  STATUS  WHEN          IMAGE  OWNER  CLUSTER  DESCRIPTION  COMMAND",  # noqa: E501
                f"j   name  failed  a second ago  i:l    {owner_printed}  dc       d            c",  # noqa: E501
            ],
            [
                "ID  NAME  STATUS  WHEN           IMAGE  OWNER  CLUSTER  DESCRIPTION  COMMAND",  # noqa: E501
                f"j   name  failed  2 seconds ago  i:l    {owner_printed}  dc       d            c",  # noqa: E501
            ],
        ]

    @pytest.mark.parametrize(
        "owner_name,owner_printed", [("owner", "<you>"), ("alice", "alice")]
    )
    def test_wide_cells(self, owner_name: str, owner_printed: str) -> None:
        jobs = [
            JobDescription(
                status=JobStatus.FAILED,
                id="job-7ee153a7-249c-4be9-965a-ba3eafb67c82",
                name="name1",
                owner=owner_name,
                cluster_name="default",
                description="some description long long long long",
                history=JobStatusHistory(
                    status=JobStatus.FAILED,
                    reason="ErrorReason",
                    description="ErrorDesc",
                    created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                    started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                    finished_at=isoparse("2017-09-25T12:28:59.759433+00:00"),
                ),
                container=Container(
                    image=RemoteImage("some-image-name", "with-long-tag"),
                    resources=Resources(16, 0.1, 0, None, False, None, None),
                    command="ls -la /some/path",
                ),
                ssh_server=URL("ssh-auth"),
                is_preemptible=True,
            ),
            JobDescription(
                status=JobStatus.PENDING,
                id="job-7ee153a7-249c-4be9-965a-ba3eafb67c84",
                name="name2",
                owner=owner_name,
                cluster_name="default",
                description="some description",
                history=JobStatusHistory(
                    status=JobStatus.PENDING,
                    reason="",
                    description="",
                    created_at=isoparse("2017-09-25T12:28:21.298672+00:00"),
                    started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                    finished_at=isoparse("2017-09-25T12:28:59.759433+00:00"),
                ),
                container=Container(
                    image=RemoteImage(
                        "some-image-name",
                        "with-long-tag",
                        registry="https://registry.neu.ro",
                        owner="bob",
                    ),
                    resources=Resources(16, 0.1, 0, None, False, None, None),
                    command="ls -la /some/path",
                ),
                ssh_server=URL("ssh-auth"),
                is_preemptible=True,
            ),
        ]
        formatter = TabularJobsFormatter(0, "owner", parse_columns(None))
        result = [item.rstrip() for item in formatter(jobs)]
        assert result == [
            f"ID                                        NAME   STATUS   WHEN         IMAGE                                     OWNER  CLUSTER  DESCRIPTION                           COMMAND",  # noqa: E501
            f"job-7ee153a7-249c-4be9-965a-ba3eafb67c82  name1  failed   Sep 25 2017  some-image-name:with-long-tag             {owner_printed}  default  some description long long long long  ls -la /some/path",  # noqa: E501
            f"job-7ee153a7-249c-4be9-965a-ba3eafb67c84  name2  pending  Sep 25 2017  image://bob/some-image-name:with-long-    {owner_printed}  default  some description                      ls -la /some/path",  # noqa: E501
            f"                                                                       tag",  # noqa: E501
        ]

    def test_custol_columns(self) -> None:
        job = JobDescription(
            status=JobStatus.FAILED,
            id="j",
            owner="owner",
            cluster_name="dc",
            name="name",
            description="d",
            history=JobStatusHistory(
                status=JobStatus.FAILED,
                reason="ErrorReason",
                description="ErrorDesc",
                created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                finished_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            ),
            container=Container(
                image=RemoteImage("i", "l"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
                command="c",
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=True,
        )

        columns = parse_columns("{status;align=right;min=20;Status Code}")
        formatter = TabularJobsFormatter(0, "owner", columns)
        result = [item.rstrip() for item in formatter([job])]

        assert result == ["         Status Code", "              failed"]


class TestNonePainter:
    def test_simple(self) -> None:
        painter = NonePainter()
        file = FileStatus(
            "File1",
            2048,
            FileStatusType.FILE,
            int(time.mktime(time.strptime("2018-01-01 03:00:00", "%Y-%m-%d %H:%M:%S"))),
            Action.READ,
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
            Action.READ,
        )
        assert painter.paint(file.name, file.type) == "'File1'"

    def test_has_quote(self) -> None:
        painter = QuotedPainter()
        file = FileStatus(
            "File1'2",
            2048,
            FileStatusType.FILE,
            int(time.mktime(time.strptime("2018-01-01 03:00:00", "%Y-%m-%d %H:%M:%S"))),
            Action.READ,
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
            Action.READ,
        )
        folder = FileStatus(
            "tmp",
            0,
            FileStatusType.DIRECTORY,
            int(time.mktime(time.strptime("2018-01-01 03:00:00", "%Y-%m-%d %H:%M:%S"))),
            Action.WRITE,
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

    def test_coloring_underline(self) -> None:
        file = FileStatus(
            "test.txt",
            1024,
            FileStatusType.FILE,
            int(time.mktime(time.strptime("2018-01-01 03:00:00", "%Y-%m-%d %H:%M:%S"))),
            Action.READ,
        )
        folder = FileStatus(
            "tmp",
            0,
            FileStatusType.DIRECTORY,
            int(time.mktime(time.strptime("2018-01-01 03:00:00", "%Y-%m-%d %H:%M:%S"))),
            Action.WRITE,
        )
        painter = GnuPainter("di=32;41:fi=0;44:no=0;46", underline=True)
        assert painter.paint(file.name, file.type) == "\x1b[0;44m\x1b[4mtest.txt\x1b[0m"
        assert painter.paint(folder.name, folder.type) == "\x1b[32;41m\x1b[4mtmp\x1b[0m"

        painter = GnuPainter("di=32;41:no=0;46", underline=True)
        assert painter.paint(file.name, file.type) == "\x1b[0;46m\x1b[4mtest.txt\x1b[0m"
        assert painter.paint(folder.name, folder.type) == "\x1b[32;41m\x1b[4mtmp\x1b[0m"

        painter = GnuPainter("no=0;46", underline=True)
        assert painter.paint(file.name, file.type) == "\x1b[0;46m\x1b[4mtest.txt\x1b[0m"
        assert painter.paint(folder.name, folder.type) == "\x1b[01;34m\x1b[4mtmp\x1b[0m"

        painter = GnuPainter("*.text=0;46", underline=True)
        assert painter.paint(file.name, file.type) == "\x1b[4mtest.txt\x1b[0m"
        assert painter.paint(folder.name, folder.type) == "\x1b[01;34m\x1b[4mtmp\x1b[0m"

        painter = GnuPainter("*.txt=0;46", underline=True)
        assert painter.paint(file.name, file.type) == "\x1b[0;46m\x1b[4mtest.txt\x1b[0m"
        assert painter.paint(folder.name, folder.type) == "\x1b[01;34m\x1b[4mtmp\x1b[0m"


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
            Action.READ,
        )
        folder = FileStatus(
            "tmp",
            0,
            FileStatusType.DIRECTORY,
            int(time.mktime(time.strptime("2018-01-01 03:00:00", "%Y-%m-%d %H:%M:%S"))),
            Action.WRITE,
        )
        painter = BSDPainter("exfxcxdxbxegedabagacad")
        assert painter.paint(file.name, file.type) == "test.txt"
        assert painter.paint(folder.name, folder.type) == click.style("tmp", fg="blue")

        painter = BSDPainter("Eafxcxdxbxegedabagacad")
        assert painter.paint(file.name, file.type) == "test.txt"
        assert painter.paint(folder.name, folder.type) == click.style(
            "tmp", fg="blue", bg="black", bold=True
        )

    def test_coloring_underline(self) -> None:
        file = FileStatus(
            "test.txt",
            1024,
            FileStatusType.FILE,
            int(time.mktime(time.strptime("2018-01-01 03:00:00", "%Y-%m-%d %H:%M:%S"))),
            Action.READ,
        )
        folder = FileStatus(
            "tmp",
            0,
            FileStatusType.DIRECTORY,
            int(time.mktime(time.strptime("2018-01-01 03:00:00", "%Y-%m-%d %H:%M:%S"))),
            Action.WRITE,
        )
        painter = BSDPainter("exfxcxdxbxegedabagacad", underline=True)
        assert painter.paint(file.name, file.type) == click.style(
            "test.txt", underline=True
        )
        assert painter.paint(folder.name, folder.type) == click.style(
            "tmp", fg="blue", underline=True
        )

        painter = BSDPainter("Eafxcxdxbxegedabagacad", underline=True)
        assert painter.paint(file.name, file.type) == click.style(
            "test.txt", underline=True
        )
        assert painter.paint(folder.name, folder.type) == click.style(
            "tmp", fg="blue", bg="black", bold=True, underline=True
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
            Action.READ,
        ),
        FileStatus(
            "File2",
            1024,
            FileStatusType.FILE,
            int(time.mktime(time.strptime("2018-10-10 13:10:10", "%Y-%m-%d %H:%M:%S"))),
            Action.READ,
        ),
        FileStatus(
            "File3 with space",
            1_024_001,
            FileStatusType.FILE,
            int(time.mktime(time.strptime("2019-02-02 05:02:02", "%Y-%m-%d %H:%M:%S"))),
            Action.READ,
        ),
    ]
    folders = [
        FileStatus(
            "Folder1",
            0,
            FileStatusType.DIRECTORY,
            int(time.mktime(time.strptime("2017-03-03 06:03:03", "%Y-%m-%d %H:%M:%S"))),
            Action.MANAGE,
        ),
        FileStatus(
            "1Folder with space",
            0,
            FileStatusType.DIRECTORY,
            int(time.mktime(time.strptime("2017-03-03 06:03:02", "%Y-%m-%d %H:%M:%S"))),
            Action.MANAGE,
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
            "-r    2K 2018-01-01 03:00:00 File1",
            "-r    1K 2018-10-10 13:10:10 File2",
            "-r 1000K 2019-02-02 05:02:02 File3 with space",
            "dm     0 2017-03-03 06:03:03 Folder1",
            "dm     0 2017-03-03 06:03:02 1Folder with space",
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
        resources = Resources(
            cpu=0.1,
            gpu=0,
            gpu_model=None,
            memory_mb=16,
            shm=False,
            tpu_type=None,
            tpu_software_version=None,
        )
        resource_formatter = ResourcesFormatter()
        assert (
            resource_formatter(resources) == "Resources:\n"
            "  Memory: 16M\n"
            "  CPU: 0.1"
        )

    def test_gpu_container(self) -> None:
        resources = Resources(
            cpu=2,
            gpu=1,
            gpu_model="nvidia-tesla-p4",
            memory_mb=1024,
            shm=False,
            tpu_type=None,
            tpu_software_version=None,
        )
        resource_formatter = ResourcesFormatter()
        assert (
            resource_formatter(resources) == "Resources:\n"
            "  Memory: 1G\n"
            "  CPU: 2.0\n"
            "  GPU: 1.0 x nvidia-tesla-p4"
        )

    def test_shm_container(self) -> None:
        resources = Resources(
            cpu=0.1,
            gpu=0,
            gpu_model=None,
            memory_mb=16,
            shm=True,
            tpu_type=None,
            tpu_software_version=None,
        )
        resource_formatter = ResourcesFormatter()
        assert (
            resource_formatter(resources) == "Resources:\n"
            "  Memory: 16M\n"
            "  CPU: 0.1\n"
            "  Additional: Extended SHM space"
        )

    def test_tpu_container(self) -> None:
        resources = Resources(
            cpu=0.1,
            gpu=0,
            gpu_model=None,
            memory_mb=16,
            shm=True,
            tpu_type="v2-8",
            tpu_software_version="1.14",
        )
        resource_formatter = ResourcesFormatter()
        assert (
            resource_formatter(resources=resources) == "Resources:\n"
            "  Memory: 16M\n"
            "  CPU: 0.1\n"
            "  TPU: v2-8/1.14\n"
            "  Additional: Extended SHM space"
        )


class TestConfigFormatter:
    async def test_output(self, root: Root) -> None:
        out = ConfigFormatter()(root.client)
        if platform == "win32":
            no = "No"
        else:
            no = "✖︎"
        assert "\n".join(
            line.rstrip() for line in click.unstyle(out).splitlines()
        ) == textwrap.dedent(
            f"""\
            User Configuration:
              User Name: user
              Current Cluster: default
              API URL: https://dev.neu.ro/api/v1
              Docker Registry URL: https://registry-dev.neu.ro
              Resource Presets:
                Name       #CPU  Memory  Preemptible  GPU
                gpu-small     7     30G       {no}      1 x nvidia-tesla-k80
                gpu-large     7     60G       {no}      1 x nvidia-tesla-v100
                cpu-small     7      2G       {no}
                cpu-large     7     14G       {no}"""
        )

    async def test_output_for_tpu_presets(
        self, make_client: Callable[..., Client], cluster_config: Cluster
    ) -> None:
        presets = dict(cluster_config.presets)

        presets["tpu-small"] = Preset(
            cpu=2,
            memory_mb=2048,
            is_preemptible=False,
            tpu_type="v3-8",
            tpu_software_version="1.14",
        )
        presets["hybrid"] = Preset(
            cpu=4,
            memory_mb=30720,
            is_preemptible=False,
            gpu=2,
            gpu_model="nvidia-tesla-v100",
            tpu_type="v3-64",
            tpu_software_version="1.14",
        )
        new_config = replace(cluster_config, presets=presets)

        client = make_client(
            "https://dev.neu.ro/api/v1", clusters={new_config.name: new_config}
        )
        out = ConfigFormatter()(client)
        if platform == "win32":
            yes = "Yes"
            no = "No"
        else:
            yes = " ✔︎"
            no = "✖︎"

        assert "\n".join(
            line.rstrip() for line in click.unstyle(out).splitlines()
        ) == textwrap.dedent(
            f"""\
            User Configuration:
              User Name: user
              Current Cluster: default
              API URL: https://dev.neu.ro/api/v1
              Docker Registry URL: https://registry-dev.neu.ro
              Resource Presets:
                Name         #CPU  Memory  Preemptible  GPU                    TPU
                gpu-small       7     30G       {no}      1 x nvidia-tesla-k80
                gpu-large       7     60G       {no}      1 x nvidia-tesla-v100
                cpu-small       7      2G       {no}
                cpu-large       7     14G       {no}
                cpu-large-p     7     14G      {yes}
                tpu-small       2      2G       {no}                             v3-8/1.14
                hybrid          4     30G       {no}      2 x nvidia-tesla-v100  v3-64/1.14"""  # noqa: E501, ignore line length
        )


bold_start = "\x1b[1m"
bold_end = "\x1b[0m"


class TestQuotaInfoFormatter:
    def test_output(self) -> None:
        quota = _QuotaInfo(
            cluster_name="default",
            gpu_time_spent=0.0,
            gpu_time_limit=0.0,
            cpu_time_spent=float((9 * 60 + 19) * 60),
            cpu_time_limit=float((9 * 60 + 39) * 60),
        )
        out = QuotaInfoFormatter()(quota)
        assert out == "\n".join(
            [
                f"{bold_start}GPU:{bold_end} spent: 00h 00m "
                "(quota: 00h 00m, left: 00h 00m)",
                f"{bold_start}CPU:{bold_end} spent: 09h 19m "
                "(quota: 09h 39m, left: 00h 20m)",
            ]
        )

    def test_output_no_quota(self) -> None:
        quota = _QuotaInfo(
            cluster_name="default",
            gpu_time_spent=0.0,
            gpu_time_limit=float("inf"),
            cpu_time_spent=float((9 * 60 + 19) * 60),
            cpu_time_limit=float("inf"),
        )
        out = QuotaInfoFormatter()(quota)
        assert out == "\n".join(
            [
                f"{bold_start}GPU:{bold_end} spent: 00h 00m (quota: infinity)",
                f"{bold_start}CPU:{bold_end} spent: 09h 19m (quota: infinity)",
            ]
        )

    def test_output_too_many_hours(self) -> None:
        quota = _QuotaInfo(
            cluster_name="default",
            gpu_time_spent=float((1 * 60 + 29) * 60),
            gpu_time_limit=float((9 * 60 + 59) * 60),
            cpu_time_spent=float((9999 * 60 + 29) * 60),
            cpu_time_limit=float((99999 * 60 + 59) * 60),
        )
        out = QuotaInfoFormatter()(quota)
        assert out == "\n".join(
            [
                f"{bold_start}GPU:{bold_end} spent: 01h 29m "
                "(quota: 09h 59m, left: 08h 30m)",
                f"{bold_start}CPU:{bold_end} spent: 9999h 29m "
                "(quota: 99999h 59m, left: 90000h 30m)",
            ]
        )

    def test_output_spent_more_than_quota_left_zero(self) -> None:
        quota = _QuotaInfo(
            cluster_name="default",
            gpu_time_spent=float(9 * 60 * 60),
            gpu_time_limit=float(1 * 60 * 60),
            cpu_time_spent=float(9 * 60 * 60),
            cpu_time_limit=float(2 * 60 * 60),
        )
        out = QuotaInfoFormatter()(quota)
        assert out == "\n".join(
            [
                f"{bold_start}GPU:{bold_end} spent: 09h 00m "
                "(quota: 01h 00m, left: 00h 00m)",
                f"{bold_start}CPU:{bold_end} spent: 09h 00m "
                "(quota: 02h 00m, left: 00h 00m)",
            ]
        )

    def test_format_time_00h_00m(self) -> None:
        out = QuotaInfoFormatter()._format_time(total_seconds=float(0 * 60))
        assert out == "00h 00m"

    def test_format_time_00h_09m(self) -> None:
        out = QuotaInfoFormatter()._format_time(total_seconds=float(9 * 60))
        assert out == "00h 09m"

    def test_format_time_01h_00m(self) -> None:
        out = QuotaInfoFormatter()._format_time(total_seconds=float(60 * 60))
        assert out == "01h 00m"

    def test_format_time_01h_10m(self) -> None:
        out = QuotaInfoFormatter()._format_time(total_seconds=float(70 * 60))
        assert out == "01h 10m"

    def test_format_time_99h_00m(self) -> None:
        out = QuotaInfoFormatter()._format_time(total_seconds=float(99 * 60 * 60))
        assert out == "99h 00m"

    def test_format_time_99h_59m(self) -> None:
        out = QuotaInfoFormatter()._format_time(
            total_seconds=float((99 * 60 + 59) * 60)
        )
        assert out == "99h 59m"

    def test_format_time_9999h_59m(self) -> None:
        out = QuotaInfoFormatter()._format_time(
            total_seconds=float((9999 * 60 + 59) * 60)
        )
        assert out == "9999h 59m"


class TestQuotaFormatter:
    def test_output(self) -> None:
        quota = _Quota(
            total_gpu_run_time_minutes=321, total_non_gpu_run_time_minutes=123,
        )
        out = QuotaFormatter()(quota)
        assert out == "\n".join(
            [f"{bold_start}GPU:{bold_end} 321m", f"{bold_start}CPU:{bold_end} 123m"]
        )

    def test_output_no_quota(self) -> None:
        quota = _Quota(
            total_non_gpu_run_time_minutes=None, total_gpu_run_time_minutes=None
        )
        out = QuotaFormatter()(quota)
        assert out == "\n".join(
            [
                f"{bold_start}GPU:{bold_end} infinity",
                f"{bold_start}CPU:{bold_end} infinity",
            ]
        )

    def test_output_only_gpu(self) -> None:
        quota = _Quota(
            total_gpu_run_time_minutes=9923, total_non_gpu_run_time_minutes=None
        )
        out = QuotaFormatter()(quota)
        assert out == "\n".join(
            [
                f"{bold_start}GPU:{bold_end} 9923m",
                f"{bold_start}CPU:{bold_end} infinity",
            ]
        )

    def test_output_only_cpu(self) -> None:
        quota = _Quota(
            total_non_gpu_run_time_minutes=3256, total_gpu_run_time_minutes=None
        )
        out = QuotaFormatter()(quota)
        assert out == "\n".join(
            [
                f"{bold_start}GPU:{bold_end} infinity",
                f"{bold_start}CPU:{bold_end} 3256m",
            ]
        )

    def test_output_zeroes(self) -> None:
        quota = _Quota(total_gpu_run_time_minutes=0, total_non_gpu_run_time_minutes=0)
        out = QuotaFormatter()(quota)
        assert out == "\n".join(
            [f"{bold_start}GPU:{bold_end} 0m", f"{bold_start}CPU:{bold_end} 0m"]
        )


class TestDockerImageProgress:
    def test_quiet_pull(self, capfd: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=True)
        formatter.pull(ImageProgressPull(RemoteImage("input"), LocalImage("output")))
        formatter.step(ImageProgressStep("message1", "layer1"))
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ""

    def test_quiet_push(self, capfd: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=True)
        formatter.push(ImageProgressPush(LocalImage("output"), RemoteImage("input")))
        formatter.step(ImageProgressStep("message1", "layer1"))
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ""

    def test_quiet_save(self, capfd: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=True)
        formatter.save(ImageProgressSave("job-id", RemoteImage("output")))
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ""

    def test_quiet_commit_started(self, capfd: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=True)
        formatter.commit_started(
            ImageCommitStarted(job_id="job-id", target_image=RemoteImage("img"))
        )
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ""

    def test_quiet_commit_finished(self, capfd: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=True)
        formatter.commit_finished(ImageCommitFinished(job_id="job-id"))
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ""

    def test_no_tty_pull(self, capfd: Any, click_tty_emulation: Any) -> None:
        formatter = DockerImageProgress.create(tty=False, quiet=False)
        formatter.pull(
            ImageProgressPull(
                RemoteImage("output", "stream", "bob", "https://registry-dev.neu.ro"),
                LocalImage("input", "latest"),
            )
        )
        formatter.step(ImageProgressStep("message1", "layer1"))
        formatter.step(ImageProgressStep("message2", "layer1"))

        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert "input:latest" in out
        assert "image://bob/output:stream" in out
        assert "message1" not in out
        assert "message2" not in out
        assert CSI not in out

    def test_no_tty_push(self, capfd: Any, click_tty_emulation: Any) -> None:
        formatter = DockerImageProgress.create(tty=False, quiet=False)
        formatter.push(
            ImageProgressPush(
                LocalImage("input", "latest"),
                RemoteImage("output", "stream", "bob", "https://registry-dev.neu.ro"),
            )
        )
        formatter.step(ImageProgressStep("message1", "layer1"))
        formatter.step(ImageProgressStep("message2", "layer1"))

        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert "input:latest" in out
        assert "image://bob/output:stream" in out
        assert "message1" not in out
        assert "message2" not in out
        assert CSI not in out

    def test_no_tty_save(self, capfd: Any) -> None:
        formatter = DockerImageProgress.create(tty=False, quiet=False)
        formatter.save(
            ImageProgressSave(
                "job-id",
                RemoteImage("output", "stream", "bob", "https://registry-dev.neu.ro"),
            )
        )
        formatter.close()
        out, err = capfd.readouterr()
        assert "Saving job 'job-id' to image 'image://bob/output:stream'" in out
        assert err == ""

    def test_no_tty_commit_started(self, capfd: Any) -> None:
        formatter = DockerImageProgress.create(tty=False, quiet=False)
        formatter.commit_started(
            ImageCommitStarted(
                job_id="job-id",
                target_image=RemoteImage(
                    "output", "stream", "bob", "https://registry-dev.neu.ro"
                ),
            )
        )
        formatter.close()
        out, err = capfd.readouterr()
        assert "Using remote image 'image://bob/output:stream'" in out
        assert f"Creating image from the job container..." in out
        assert err == ""

    def test_no_tty_commit_finished(self, capfd: Any) -> None:
        formatter = DockerImageProgress.create(tty=False, quiet=False)
        formatter.commit_finished(ImageCommitFinished(job_id="job-id"))
        formatter.close()
        out, err = capfd.readouterr()
        assert out.startswith("Image created")
        assert err == ""

    def test_tty_pull(self, capfd: Any, click_tty_emulation: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=False)
        formatter.pull(
            ImageProgressPull(
                RemoteImage("output", "stream", "bob", "https://registry-dev.neu.ro"),
                LocalImage("input", "latest"),
            )
        )
        formatter.step(ImageProgressStep("message1", "layer1"))
        formatter.step(ImageProgressStep("message2", "layer1"))
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert "input:latest" in out
        assert "image://bob/output:stream" in out
        assert "message1" in out
        assert "message2" in out
        assert CSI in out

    def test_tty_push(self, capfd: Any, click_tty_emulation: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=False)
        formatter.push(
            ImageProgressPush(
                LocalImage("input", "latest"),
                RemoteImage("output", "stream", "bob", "https://registry-dev.neu.ro"),
            )
        )
        formatter.step(ImageProgressStep("message1", "layer1"))
        formatter.step(ImageProgressStep("message2", "layer1"))
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert "input:latest" in out
        assert "image://bob/output:stream" in out
        assert "message1" in out
        assert "message2" in out
        assert CSI in out

    def test_tty_save(self, capfd: Any, click_tty_emulation: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=False)
        formatter.save(
            ImageProgressSave(
                "job-id",
                RemoteImage("output", "stream", "bob", "https://registry-dev.neu.ro"),
            )
        )
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert "job-id" in out
        assert "image://bob/output:stream" in out
        assert CSI in out

    def test_tty_commit_started(self, capfd: Any, click_tty_emulation: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=False)
        formatter.commit_started(
            ImageCommitStarted(job_id="job-id", target_image=RemoteImage("img"))
        )
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert "img" in out
        assert CSI in out

    def test_tty_commit_finished(self, capfd: Any, click_tty_emulation: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=False)
        formatter.commit_finished(ImageCommitFinished(job_id="job-id"))
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out.startswith("Image created")
        assert CSI not in out  # no styled strings


class TestClusterUserFormatter:
    def test_cluster_list(self) -> None:
        formatter = ClusterUserFormatter()
        users = [
            _ClusterUser(user_name="denis", role=_ClusterUserRoleType("admin")),
            _ClusterUser(user_name="andrew", role=_ClusterUserRoleType("manager")),
            _ClusterUser(user_name="ivan", role=_ClusterUserRoleType("user")),
            _ClusterUser(user_name="alex", role=_ClusterUserRoleType("user")),
        ]
        expected_out = [
            "\x1b[1mName\x1b[0m    \x1b[1mRole\x1b[0m   ",
            "denis   admin  ",
            "andrew  manager",
            "ivan    user   ",
            "alex    user   ",
        ]
        assert formatter(users) == expected_out


class TestClustersFormatter:
    def _create_node_pool(
        self,
        is_gpu: bool = False,
        is_tpu_enabled: bool = False,
        is_preemptible: bool = False,
        has_idle: bool = False,
    ) -> _NodePool:
        return _NodePool(
            min_size=1,
            max_size=2,
            idle_size=1 if has_idle else 0,
            machine_type="n1-highmem-8",
            available_cpu=7.0,
            available_memory_mb=46080,
            gpu=1 if is_gpu else 0,
            gpu_model="nvidia-tesla-k80" if is_gpu else None,
            is_preemptible=is_preemptible,
            is_tpu_enabled=is_tpu_enabled,
        )

    @property
    def _yes(self) -> str:
        return "Yes" if platform == "win32" else " ✔︎"

    @property
    def _no(self) -> str:
        return "No" if platform == "win32" else "✖︎"

    def test_cluster_list(self) -> None:
        formatter = ClustersFormatter()
        clusters = [_Cluster(name="default", status="deployed")]
        expected_out = textwrap.dedent(
            """\
            \x1b[1mdefault:\x1b[0m
              \x1b[1mStatus: \x1b[0mDeployed"""
        )
        assert "\n".join(formatter(clusters)) == expected_out

    def test_cluster_with_cloud_provider_storage_list(self) -> None:
        formatter = ClustersFormatter()
        clusters = [
            _Cluster(
                name="default",
                status="deployed",
                cloud_provider=_CloudProvider(
                    type="gcp",
                    region="us-central1",
                    zones=["us-central1-a", "us-central1-c"],
                    node_pools=[],
                    storage=_Storage(description="Filestore"),
                ),
            )
        ]
        expected_out = textwrap.dedent(
            """\
            \x1b[1mdefault:\x1b[0m
              \x1b[1mStatus: \x1b[0mDeployed
              \x1b[1mCloud: \x1b[0mgcp
              \x1b[1mRegion: \x1b[0mus-central1
              \x1b[1mZones: \x1b[0mus-central1-a, us-central1-c
              \x1b[1mStorage: \x1b[0mFilestore"""
        )
        assert "\n".join(formatter(clusters)) == expected_out

    def test_cluster_with_cloud_provider_node_pool_list(self) -> None:
        formatter = ClustersFormatter()
        clusters = [
            _Cluster(
                name="default",
                status="deployed",
                cloud_provider=_CloudProvider(
                    type="gcp",
                    region="us-central1",
                    zones=[],
                    node_pools=[
                        self._create_node_pool(is_preemptible=True),
                        self._create_node_pool(is_gpu=True),
                    ],
                    storage=None,
                ),
            )
        ]
        expected_out = textwrap.dedent(
            f"""\
            \x1b[1mdefault:\x1b[0m
              \x1b[1mStatus: \x1b[0mDeployed
              \x1b[1mCloud: \x1b[0mgcp
              \x1b[1mRegion: \x1b[0mus-central1
              \x1b[1mNode pools:\x1b[0m
                Machine       CPU  Memory  Preemptible                   GPU  Min  Max
                n1-highmem-8  7.0     45G      {self._yes}                              1    2
                n1-highmem-8  7.0     45G       {self._no}      1 x nvidia-tesla-k80    1    2"""  # noqa: E501, ignore line length
        )
        assert "\n".join(formatter(clusters)) == expected_out

    def test_cluster_with_cloud_provider_node_pool_tpu_idle_list(self) -> None:
        formatter = ClustersFormatter()
        clusters = [
            _Cluster(
                name="default",
                status="deployed",
                cloud_provider=_CloudProvider(
                    type="gcp",
                    region="us-central1",
                    zones=[],
                    node_pools=[
                        self._create_node_pool(is_tpu_enabled=True, has_idle=True),
                        self._create_node_pool(),
                    ],
                    storage=None,
                ),
            )
        ]
        expected_out = textwrap.dedent(
            f"""\
            \x1b[1mdefault:\x1b[0m
              \x1b[1mStatus: \x1b[0mDeployed
              \x1b[1mCloud: \x1b[0mgcp
              \x1b[1mRegion: \x1b[0mus-central1
              \x1b[1mNode pools:\x1b[0m
                Machine       CPU  Memory  Preemptible  GPU  TPU  Min  Max  Idle
                n1-highmem-8  7.0     45G       {self._no}           {self._yes}    1    2     1
                n1-highmem-8  7.0     45G       {self._no}            {self._no}    1    2     0"""  # noqa: E501, ignore line length
        )
        assert "\n".join(formatter(clusters)) == expected_out
