from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import click
import pytest
from dateutil.parser import isoparse
from yarl import URL

from neuromation.api import (
    Container,
    HTTPPort,
    JobDescription,
    JobRestartPolicy,
    JobStatus,
    JobStatusHistory,
    JobTelemetry,
    RemoteImage,
    Resources,
    Volume,
)
from neuromation.api.parsing_utils import _ImageNameParser
from neuromation.cli.formatters import (
    JobFormatter,
    JobStartProgress,
    JobStatusFormatter,
    JobTelemetryFormatter,
    SimpleJobsFormatter,
    TabularJobsFormatter,
)
from neuromation.cli.formatters.jobs import (
    ResourcesFormatter,
    TabularJobRow,
    format_timedelta,
)
from neuromation.cli.formatters.utils import image_formatter, uri_formatter
from neuromation.cli.parse_utils import parse_columns
from neuromation.cli.printer import CSI


TEST_JOB_ID = "job-ad09fe07-0c64-4d32-b477-3b737d215621"
TEST_JOB_NAME = "test-job-name"


@pytest.fixture
def job_descr_no_name() -> JobDescription:
    return JobDescription(
        status=JobStatus.PENDING,
        id=TEST_JOB_ID,
        owner="owner",
        cluster_name="default",
        uri=URL(f"job://default/owner/{TEST_JOB_ID}"),
        history=JobStatusHistory(
            status=JobStatus.PENDING,
            reason="ErrorReason",
            description="ErrorDesc",
            created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
            started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
            finished_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
        ),
        container=Container(
            image=RemoteImage.new_external_image(name="ubuntu", tag="latest"),
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
        uri=URL(f"job://default/owner/{TEST_JOB_ID}"),
        history=JobStatusHistory(
            status=JobStatus.PENDING,
            reason="ErrorReason",
            description="ErrorDesc",
            created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
            started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
            finished_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
        ),
        container=Container(
            image=RemoteImage.new_external_image(name="ubuntu", tag="latest"),
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
            uri=URL("job://default/test-user/test-job"),
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
                image=RemoteImage.new_external_image(name="test-image"),
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
            uri=URL("job://default/test-user/test-job"),
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
                image=RemoteImage.new_external_image(name="test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
                http=HTTPPort(port=80, requires_auth=True),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = JobStatusFormatter(uri_formatter=uri_fmtr)(description)
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

    def test_job_with_tags(self) -> None:
        description = JobDescription(
            status=JobStatus.FAILED,
            owner="test-user",
            cluster_name="default",
            id="test-job",
            uri=URL("job://default/test-user/test-job"),
            tags=["tag1", "tag2", "tag3"],
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
                image=RemoteImage.new_external_image(name="test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
                http=HTTPPort(port=80, requires_auth=True),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = JobStatusFormatter(uri_formatter=uri_fmtr)(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Tags: tag1, tag2, tag3\n"
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

    def test_job_with_life_span_with_value(self) -> None:
        description = JobDescription(
            status=JobStatus.FAILED,
            owner="test-user",
            cluster_name="default",
            id="test-job",
            uri=URL("job://default/test-user/test-job"),
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
                image=RemoteImage.new_external_image(name="test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
                http=HTTPPort(port=80, requires_auth=True),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
            life_span=1.0 * ((60 * 60 * 24 * 1) + (60 * 60 * 2) + (60 * 3) + 4),
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = JobStatusFormatter(uri_formatter=uri_fmtr)(description)
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
            "Life span: 1d2h3m4s\n"
            "Http URL: http://local.host.test/\n"
            "Http authentication: True\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 123\n"
            "===Description===\n"
            "ErrorDesc\n================="
        )

    def test_job_with_life_span_without_value(self) -> None:
        description = JobDescription(
            status=JobStatus.FAILED,
            owner="test-user",
            cluster_name="default",
            id="test-job",
            uri=URL("job://default/test-user/test-job"),
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
                image=RemoteImage.new_external_image(name="test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
                http=HTTPPort(port=80, requires_auth=True),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
            life_span=0.0,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = JobStatusFormatter(uri_formatter=uri_fmtr)(description)
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
            "Life span: no limit\n"
            "Http URL: http://local.host.test/\n"
            "Http authentication: True\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 123\n"
            "===Description===\n"
            "ErrorDesc\n================="
        )

    def test_job_with_restart_policy(self) -> None:
        description = JobDescription(
            status=JobStatus.FAILED,
            owner="test-user",
            cluster_name="default",
            id="test-job",
            uri=URL("job://default/test-user/test-job"),
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
                image=RemoteImage.new_external_image(name="test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
                http=HTTPPort(port=80, requires_auth=True),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
            restart_policy=JobRestartPolicy.ALWAYS,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = JobStatusFormatter(uri_formatter=uri_fmtr)(description)
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
            "Restart policy: always\n"
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
            uri=URL("job://default/test-user/test-job"),
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
                image=RemoteImage.new_external_image(name="test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
                http=HTTPPort(port=80, requires_auth=True),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = JobStatusFormatter(uri_formatter=uri_fmtr)(description)
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
                image=RemoteImage.new_external_image(name="test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=True,
            owner="owner",
            cluster_name="default",
            uri=URL("job://default/owner/test-job"),
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = JobStatusFormatter(uri_formatter=uri_fmtr)(description)
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
                image=RemoteImage.new_external_image(name="test-image"),
                command="test-command",
                resources=Resources(16, 0.1, 0, None, False, None, None),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=True,
            owner="owner",
            cluster_name="default",
            uri=URL("job://default/owner/test-job"),
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = JobStatusFormatter(uri_formatter=uri_fmtr)(description)
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
                image=RemoteImage.new_external_image(name="test-image"),
                command="test-command",
                resources=Resources(16, 0.1, 0, None, False, None, None),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=True,
            owner="owner",
            cluster_name="default",
            uri=URL("job://default/owner/test-job"),
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = JobStatusFormatter(uri_formatter=uri_fmtr)(description)
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
            uri=URL("job://default/test-user/test-job"),
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
                image=RemoteImage.new_external_image(name="test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
            internal_hostname="host.local",
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = JobStatusFormatter(uri_formatter=uri_fmtr)(description)
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
            uri=URL("job://default/test-user/test-job"),
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
                image=RemoteImage.new_external_image(name="test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
            internal_hostname="host.local",
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = JobStatusFormatter(uri_formatter=uri_fmtr)(description)
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

    def test_job_with_volumes_short(self) -> None:
        description = JobDescription(
            status=JobStatus.FAILED,
            owner="test-user",
            cluster_name="default",
            id="test-job",
            uri=URL("job://default/test-user/test-job"),
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
                image=RemoteImage.new_neuro_image(
                    name="test-image",
                    tag="sometag",
                    registry="https://registry.neu.ro",
                    owner="test-user",
                    cluster_name="test-cluster",
                ),
                resources=Resources(16, 0.1, 0, None, False, None, None),
                http=HTTPPort(port=80, requires_auth=True),
                volumes=[
                    Volume(
                        storage_uri=URL("storage://test-cluster/otheruser/ro"),
                        container_path="/mnt/ro",
                        read_only=True,
                    ),
                    Volume(
                        storage_uri=URL("storage://test-cluster/test-user/rw"),
                        container_path="/mnt/rw",
                        read_only=False,
                    ),
                    Volume(
                        storage_uri=URL("storage://othercluster/otheruser/ro"),
                        container_path="/mnt/ro2",
                        read_only=True,
                    ),
                ],
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = JobStatusFormatter(uri_formatter=uri_fmtr)(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Name: test-job-name\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: image:test-image:sometag\n"
            "Command: test-command\n"
            f"{resource_formatter(description.container.resources)}\n"
            "Preemptible: False\n"
            "Volumes:\n"
            "  /mnt/ro   storage:/otheruser/ro                READONLY\n"
            "  /mnt/rw   storage:rw                                   \n"
            "  /mnt/ro2  storage://othercluster/otheruser/ro  READONLY\n"
            "Http URL: http://local.host.test/\n"
            "Http authentication: True\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 123\n"
            "===Description===\n"
            "ErrorDesc\n================="
        )

    def test_job_with_volumes_long(self) -> None:
        description = JobDescription(
            status=JobStatus.FAILED,
            owner="test-user",
            cluster_name="default",
            id="test-job",
            uri=URL("job://default/test-user/test-job"),
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
                image=RemoteImage.new_neuro_image(
                    name="test-image",
                    tag="sometag",
                    registry="https://registry.neu.ro",
                    owner="test-user",
                    cluster_name="test-cluster",
                ),
                resources=Resources(16, 0.1, 0, None, False, None, None),
                http=HTTPPort(port=80, requires_auth=True),
                volumes=[
                    Volume(
                        storage_uri=URL("storage://test-cluster/otheruser/ro"),
                        container_path="/mnt/ro",
                        read_only=True,
                    ),
                    Volume(
                        storage_uri=URL("storage://test-cluster/test-user/rw"),
                        container_path="/mnt/rw",
                        read_only=False,
                    ),
                ],
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
        )

        status = JobStatusFormatter(uri_formatter=str)(description)
        resource_formatter = ResourcesFormatter()
        assert (
            status == "Job: test-job\n"
            "Name: test-job-name\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: image://test-cluster/test-user/test-image:sometag\n"
            "Command: test-command\n"
            f"{resource_formatter(description.container.resources)}\n"
            "Preemptible: False\n"
            "Volumes:\n"
            "  /mnt/ro  storage://test-cluster/otheruser/ro  READONLY\n"
            "  /mnt/rw  storage://test-cluster/test-user/rw          \n"
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


class TestJobStatusFormatter:
    def test_format_timedelta(self) -> None:
        delta = timedelta(days=1, hours=2, minutes=3, seconds=4)
        assert format_timedelta(delta) == "1d2h3m4s"

    def test_format_timedelta_no_days(self) -> None:
        delta = timedelta(hours=2, minutes=3, seconds=4)
        assert format_timedelta(delta) == "2h3m4s"

    def test_format_timedelta_no_hours(self) -> None:
        delta = timedelta(days=1, minutes=3, seconds=4)
        assert format_timedelta(delta) == "1d3m4s"

    def test_format_timedelta_no_minutes(self) -> None:
        delta = timedelta(days=1, hours=2, seconds=4)
        assert format_timedelta(delta) == "1d2h4s"

    def test_format_timedelta_no_seconds(self) -> None:
        delta = timedelta(days=1, hours=2, minutes=3)
        assert format_timedelta(delta) == "1d2h3m"

    def test_format_timedelta_overfill(self) -> None:
        minutes = 60 * 24 * 30 + 20
        delta = timedelta(minutes=minutes, seconds=10)
        assert format_timedelta(delta) == "30d20m10s"

    def test_format_timedelta_zero(self) -> None:
        delta = timedelta(0)
        assert format_timedelta(delta) == ""

    def test_format_timedelta_negative(self) -> None:
        delta = timedelta(-1)
        with pytest.raises(ValueError, match="Invalid delta"):
            assert format_timedelta(delta)


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
                uri=URL("job://default/owner/job-42687e7c-6c76-4857-a6a7-1166f8295391"),
                history=JobStatusHistory(
                    status=JobStatus.PENDING,
                    reason="ErrorReason",
                    description="ErrorDesc",
                    created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                    started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                    finished_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                ),
                container=Container(
                    image=RemoteImage.new_external_image(name="ubuntu", tag="latest"),
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
                uri=URL("job://default/owner/job-cf33bd55-9e3b-4df7-a894-9c148a908a66"),
                history=JobStatusHistory(
                    status=JobStatus.FAILED,
                    reason="ErrorReason",
                    description="ErrorDesc",
                    created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                    started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                    finished_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                ),
                container=Container(
                    image=RemoteImage.new_external_image(name="ubuntu", tag="latest"),
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
    image_parser = _ImageNameParser(
        "bob", "test-cluster", URL("https://registry-test.neu.ro")
    )

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
            uri=URL("job://default/owner/job-1f5ab792-e534-4bb4-be56-8af1ce722692"),
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
            self._job_descr_with_status(JobStatus.RUNNING, name="job-name"),
            "owner",
            image_formatter=str,
        )
        assert row.name == "job-name"

    def test_without_job_name(self) -> None:
        row = TabularJobRow.from_job(
            self._job_descr_with_status(JobStatus.RUNNING, name=None),
            "owner",
            image_formatter=str,
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
        row = TabularJobRow.from_job(
            self._job_descr_with_status(status), "owner", image_formatter=str
        )
        assert row.status == f"{status}"
        assert row.when == date

    def test_image_from_registry_parsing_short(self) -> None:
        uri_fmtr = uri_formatter(username="bob", cluster_name="test-cluster")
        image_fmtr = image_formatter(uri_formatter=uri_fmtr)
        row = TabularJobRow.from_job(
            self._job_descr_with_status(
                JobStatus.PENDING, "registry-test.neu.ro/bob/swiss-box:red",
            ),
            "bob",
            image_formatter=image_fmtr,
        )
        assert row.image == "image:swiss-box:red"
        assert row.name == ""

    def test_image_from_registry_parsing_long(self) -> None:
        row = TabularJobRow.from_job(
            self._job_descr_with_status(
                JobStatus.PENDING, "registry-test.neu.ro/bob/swiss-box:red",
            ),
            "owner",
            image_formatter=str,
        )
        assert row.image == "image://test-cluster/bob/swiss-box:red"
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
    image_parser = _ImageNameParser(
        "bob", "test-cluster", URL("https://registry-test.neu.ro")
    )

    def test_empty(self) -> None:
        formatter = TabularJobsFormatter(
            0, "owner", parse_columns(None), image_formatter=str
        )
        result = [item for item in formatter([])]
        assert result == ["  ".join(self.columns)]

    def test_width_cutting(self) -> None:
        formatter = TabularJobsFormatter(
            10, "owner", parse_columns(None), image_formatter=str
        )
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
            uri=URL(f"job://dc/{owner_name}/j"),
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
                image=RemoteImage.new_external_image(name="i", tag="l"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
                command="c",
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=True,
        )
        formatter = TabularJobsFormatter(
            0, "owner", parse_columns(None), image_formatter=str
        )
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
                uri=URL(
                    f"job://default/{owner_name}/"
                    f"job-7ee153a7-249c-4be9-965a-ba3eafb67c82"
                ),
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
                    image=RemoteImage.new_external_image(
                        name="some-image-name", tag="with-long-tag"
                    ),
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
                uri=URL(
                    f"job://default/{owner_name}/"
                    f"job-7ee153a7-249c-4be9-965a-ba3eafb67c84"
                ),
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
                    image=RemoteImage.new_neuro_image(
                        name="some-image-name",
                        tag="with-long-tag",
                        registry="https://registry.neu.ro",
                        owner="bob",
                        cluster_name="test-cluster",
                    ),
                    resources=Resources(16, 0.1, 0, None, False, None, None),
                    command="ls -la /some/path",
                ),
                ssh_server=URL("ssh-auth"),
                is_preemptible=True,
            ),
        ]
        formatter = TabularJobsFormatter(
            0, "owner", parse_columns(None), image_formatter=str
        )
        result = [item.rstrip() for item in formatter(jobs)]
        assert result == [
            f"ID                                        NAME   STATUS   WHEN         IMAGE                                     OWNER  CLUSTER  DESCRIPTION                           COMMAND",  # noqa: E501
            f"job-7ee153a7-249c-4be9-965a-ba3eafb67c82  name1  failed   Sep 25 2017  some-image-name:with-long-tag             {owner_printed}  default  some description long long long long  ls -la /some/path",  # noqa: E501
            f"job-7ee153a7-249c-4be9-965a-ba3eafb67c84  name2  pending  Sep 25 2017  image://test-cluster/bob/some-image-      {owner_printed}  default  some description                      ls -la /some/path",  # noqa: E501
            f"                                                                       name:with-long-tag",  # noqa: E501
        ]

    def test_custol_columns(self) -> None:
        job = JobDescription(
            status=JobStatus.FAILED,
            id="j",
            owner="owner",
            cluster_name="dc",
            uri=URL("job://dc/owner/j"),
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
                image=RemoteImage.new_external_image(name="i", tag="l"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
                command="c",
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=True,
        )

        columns = parse_columns("{status;align=right;min=20;Status Code}")
        formatter = TabularJobsFormatter(0, "owner", columns, image_formatter=str)
        result = [item.rstrip() for item in formatter([job])]

        assert result == ["         Status Code", "              failed"]


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
            "  Memory: 16.0M\n"
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
            "  Memory: 1.0G\n"
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
            "  Memory: 16.0M\n"
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
            "  Memory: 16.0M\n"
            "  CPU: 0.1\n"
            "  TPU: v2-8/1.14\n"
            "  Additional: Extended SHM space"
        )
