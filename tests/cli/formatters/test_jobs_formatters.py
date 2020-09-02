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
from neuromation.api.parser import SecretFile
from neuromation.api.parsing_utils import _ImageNameParser
from neuromation.cli.formatters.jobs import (
    JobStartProgress,
    JobStatusFormatter,
    JobTelemetryFormatter,
    ResourcesFormatter,
    SimpleJobsFormatter,
    TabularJobRow,
    TabularJobsFormatter,
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


class TestJobStartProgress:
    def make_job(
        self,
        status: JobStatus,
        reason: str,
        *,
        name: Optional[str] = None,
        life_span: Optional[float] = None,
    ) -> JobDescription:
        return JobDescription(
            name=name,
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
            life_span=life_span,
        )

    def strip(self, text: str) -> str:
        return click.unstyle(text).strip()

    def test_quiet(self, capfd: Any) -> None:
        job = self.make_job(JobStatus.PENDING, "")
        progress = JobStartProgress.create(tty=True, color=True, quiet=True)
        progress.begin(job)
        out, err = capfd.readouterr()
        assert err == ""
        assert out == "test-job\n"
        progress.step(job)
        progress.end(job)
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ""

    def test_no_tty_begin(self, capfd: Any, click_tty_emulation: Any) -> None:
        progress = JobStartProgress.create(tty=False, color=True, quiet=False)
        progress.begin(self.make_job(JobStatus.PENDING, ""))
        out, err = capfd.readouterr()
        assert err == ""
        assert "test-job" in out
        assert CSI not in out

    def test_no_tty_begin_with_name(self, capfd: Any, click_tty_emulation: Any) -> None:
        progress = JobStartProgress.create(tty=False, color=True, quiet=False)
        progress.begin(self.make_job(JobStatus.PENDING, "", name="job-name"))
        out, err = capfd.readouterr()
        assert err == ""
        assert "test-job" in out
        assert "job-name" in out
        assert CSI not in out

    def test_no_tty_step(self, capfd: Any, click_tty_emulation: Any) -> None:
        progress = JobStartProgress.create(tty=False, color=True, quiet=False)
        progress.step(self.make_job(JobStatus.PENDING, ""))
        progress.step(self.make_job(JobStatus.PENDING, ""))
        progress.step(self.make_job(JobStatus.RUNNING, "reason"))
        out, err = capfd.readouterr()
        assert err == ""
        assert "pending" in out
        assert "running" in out
        assert "reason (ErrorDesc)" in out
        assert out.count("pending") == 1
        assert CSI not in out

    def test_no_tty_end(self, capfd: Any, click_tty_emulation: Any) -> None:
        progress = JobStartProgress.create(tty=False, color=True, quiet=False)
        progress.end(self.make_job(JobStatus.RUNNING, ""))
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ""

    def test_tty_begin(self, capfd: Any, click_tty_emulation: Any) -> None:
        progress = JobStartProgress.create(tty=True, color=True, quiet=False)
        progress.begin(self.make_job(JobStatus.PENDING, ""))
        out, err = capfd.readouterr()
        assert err == ""
        assert "test-job" in out
        assert CSI in out

    def test_tty_begin_with_name(self, capfd: Any, click_tty_emulation: Any) -> None:
        progress = JobStartProgress.create(tty=True, color=True, quiet=False)
        progress.begin(self.make_job(JobStatus.PENDING, "", name="job-name"))
        out, err = capfd.readouterr()
        assert err == ""
        assert "test-job" in out
        assert "job-name" in out
        assert CSI in out

    def test_tty_step(self, capfd: Any, click_tty_emulation: Any) -> None:
        progress = JobStartProgress.create(tty=True, color=True, quiet=False)
        progress.step(self.make_job(JobStatus.PENDING, ""))
        progress.step(self.make_job(JobStatus.PENDING, ""))
        progress.step(self.make_job(JobStatus.RUNNING, "reason"))
        out, err = capfd.readouterr()
        assert err == ""
        assert "pending" in out
        assert "running" in out
        assert "reason" in out
        assert "(ErrorDesc)" in out
        assert out.count("pending") != 1
        assert CSI in out

    def test_tty_end(self, capfd: Any, click_tty_emulation: Any) -> None:
        progress = JobStartProgress.create(tty=True, color=True, quiet=False)
        progress.end(self.make_job(JobStatus.RUNNING, ""))
        out, err = capfd.readouterr()
        assert err == ""
        assert "http://local.host.test/" in out
        assert CSI in out

    def test_tty_end_with_life_span(self, capfd: Any, click_tty_emulation: Any) -> None:
        progress = JobStartProgress.create(tty=True, color=True, quiet=False)
        progress.end(self.make_job(JobStatus.RUNNING, "", life_span=24 * 3600))
        out, err = capfd.readouterr()
        assert err == ""
        assert "http://local.host.test/" in out
        assert "The job will die in a day." in out
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
        status = click.unstyle(JobStatusFormatter(uri_formatter=uri_fmtr)(description))
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Name: test-job-name\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource}\n"
            "TTY: False\n"
            "Http URL: http://local.host.test/\n"
            "Http port: 80\n"
            "Http authentication: True\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 123\n"
            "=== Description ===\n"
            "ErrorDesc\n==================="
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
        status = click.unstyle(JobStatusFormatter(uri_formatter=uri_fmtr)(description))
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Tags: tag1, tag2, tag3\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource}\n"
            "TTY: False\n"
            "Http URL: http://local.host.test/\n"
            "Http port: 80\n"
            "Http authentication: True\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 123\n"
            "=== Description ===\n"
            "ErrorDesc\n==================="
        )

    def test_job_with_tags_wrap_tags(self) -> None:
        description = JobDescription(
            status=JobStatus.FAILED,
            owner="test-user",
            cluster_name="default",
            id="test-job",
            uri=URL("job://default/test-user/test-job"),
            tags=["long-tag-1", "long-tag-2", "long-tag-3", "long-tag-4"],
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
        status = click.unstyle(
            JobStatusFormatter(uri_formatter=uri_fmtr, width=50)(description)
        )
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Tags: long-tag-1, long-tag-2, long-tag-3,\n"
            "      long-tag-4\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource}\n"
            "TTY: False\n"
            "Http URL: http://local.host.test/\n"
            "Http port: 80\n"
            "Http authentication: True\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 123\n"
            "=== Description ===\n"
            "ErrorDesc\n==================="
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
        status = click.unstyle(JobStatusFormatter(uri_formatter=uri_fmtr)(description))
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource}\n"
            "Life span: 1d2h3m4s\n"
            "TTY: False\n"
            "Http URL: http://local.host.test/\n"
            "Http port: 80\n"
            "Http authentication: True\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 123\n"
            "=== Description ===\n"
            "ErrorDesc\n==================="
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
        status = click.unstyle(JobStatusFormatter(uri_formatter=uri_fmtr)(description))
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource}\n"
            "Life span: no limit\n"
            "TTY: False\n"
            "Http URL: http://local.host.test/\n"
            "Http port: 80\n"
            "Http authentication: True\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 123\n"
            "=== Description ===\n"
            "ErrorDesc\n==================="
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
        status = click.unstyle(JobStatusFormatter(uri_formatter=uri_fmtr)(description))
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource}\n"
            "Restart policy: always\n"
            "TTY: False\n"
            "Http URL: http://local.host.test/\n"
            "Http port: 80\n"
            "Http authentication: True\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 123\n"
            "=== Description ===\n"
            "ErrorDesc\n==================="
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
        status = click.unstyle(JobStatusFormatter(uri_formatter=uri_fmtr)(description))
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource}\n"
            "TTY: False\n"
            "Http URL: http://local.host.test/\n"
            "Http port: 80\n"
            "Http authentication: True\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 321\n"
            "=== Description ===\n"
            "ErrorDesc\n==================="
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
        status = click.unstyle(JobStatusFormatter(uri_formatter=uri_fmtr)(description))
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Owner: owner\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: pending\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource}\n"
            "Preemptible: True\n"
            "TTY: False\n"
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
                tty=True,
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=True,
            owner="owner",
            cluster_name="default",
            uri=URL("job://default/owner/test-job"),
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = click.unstyle(JobStatusFormatter(uri_formatter=uri_fmtr)(description))
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Owner: owner\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: pending (ContainerCreating)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource}\n"
            "Preemptible: True\n"
            "TTY: True\n"
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
        status = click.unstyle(JobStatusFormatter(uri_formatter=uri_fmtr)(description))
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Owner: owner\n"
            "Cluster: default\n"
            "Status: pending (ContainerCreating)\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource}\n"
            "Preemptible: True\n"
            "TTY: False\n"
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
        status = click.unstyle(JobStatusFormatter(uri_formatter=uri_fmtr)(description))
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: running\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource}\n"
            "TTY: False\n"
            "Internal Hostname: host.local\n"
            "Http URL: http://local.host.test/\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:24.759433+00:00"
        )

    def test_running_named_job(self) -> None:
        description = JobDescription(
            status=JobStatus.RUNNING,
            owner="test-user",
            name="test-job",
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
            internal_hostname_named="test-job--test-owner.local",
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = click.unstyle(JobStatusFormatter(uri_formatter=uri_fmtr)(description))
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Name: test-job\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: running\n"
            "Image: test-image\n"
            "Command: test-command\n"
            f"{resource}\n"
            "TTY: False\n"
            "Internal Hostname: host.local\n"
            "Internal Hostname Named: test-job--test-owner.local\n"
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
        status = click.unstyle(JobStatusFormatter(uri_formatter=uri_fmtr)(description))
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: running\n"
            "Image: test-image\n"
            "Entrypoint: /usr/bin/make\n"
            "Command: test\n"
            f"{resource}\n"
            "TTY: False\n"
            "Internal Hostname: host.local\n"
            "Http URL: http://local.host.test/\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:24.759433+00:00"
        )

    def test_job_with_environment(self) -> None:
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
                env={"ENV_NAME_1": "__value1__", "ENV_NAME_2": "**value2**"},
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = click.unstyle(JobStatusFormatter(uri_formatter=uri_fmtr)(description))
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Name: test-job-name\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: image:test-image:sometag\n"
            "Command: test-command\n"
            f"{resource}\n"
            "TTY: False\n"
            "Http URL: http://local.host.test/\n"
            "Http port: 80\n"
            "Http authentication: True\n"
            "Environment:\n"
            "  ENV_NAME_1=__value1__\n"
            "  ENV_NAME_2=**value2**\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 123\n"
            "=== Description ===\n"
            "ErrorDesc\n==================="
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
                        storage_uri=URL("storage://test-cluster/otheruser/_ro_"),
                        container_path="/mnt/_ro_",
                        read_only=True,
                    ),
                    Volume(
                        storage_uri=URL("storage://test-cluster/test-user/rw"),
                        container_path="/mnt/rw",
                        read_only=False,
                    ),
                    Volume(
                        storage_uri=URL("storage://othercluster/otheruser/ro"),
                        container_path="/mnt/ro",
                        read_only=True,
                    ),
                ],
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = click.unstyle(JobStatusFormatter(uri_formatter=uri_fmtr)(description))
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Name: test-job-name\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: image:test-image:sometag\n"
            "Command: test-command\n"
            f"{resource}\n"
            "TTY: False\n"
            "Volumes:\n"
            "  /mnt/_ro_  storage:/otheruser/_ro_              READONLY\n"
            "  /mnt/rw    storage:rw                                   \n"
            "  /mnt/ro    storage://othercluster/otheruser/ro  READONLY\n"
            "Http URL: http://local.host.test/\n"
            "Http port: 80\n"
            "Http authentication: True\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 123\n"
            "=== Description ===\n"
            "ErrorDesc\n==================="
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

        status = click.unstyle(JobStatusFormatter(uri_formatter=str)(description))
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Name: test-job-name\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: image://test-cluster/test-user/test-image:sometag\n"
            "Command: test-command\n"
            f"{resource}\n"
            "TTY: False\n"
            "Volumes:\n"
            "  /mnt/ro  storage://test-cluster/otheruser/ro  READONLY\n"
            "  /mnt/rw  storage://test-cluster/test-user/rw          \n"
            "Http URL: http://local.host.test/\n"
            "Http port: 80\n"
            "Http authentication: True\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 123\n"
            "=== Description ===\n"
            "ErrorDesc\n==================="
        )

    def test_job_with_secrets_short(self) -> None:
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
                        storage_uri=URL("storage://test-cluster/test-user/rw"),
                        container_path="/mnt/rw",
                        read_only=False,
                    ),
                ],
                secret_files=[
                    SecretFile(
                        URL("secret://test-cluster/test-user/secret1"),
                        "/var/run/secret1",
                    ),
                    SecretFile(
                        URL("secret://test-cluster/otheruser/secret2"),
                        "/var/run/secret2",
                    ),
                    SecretFile(
                        URL("secret://othercluster/otheruser/secret3"),
                        "/var/run/secret3",
                    ),
                ],
                env={"ENV_NAME_0": "somevalue"},
                secret_env={
                    "ENV_NAME_1": URL("secret://test-cluster/test-user/secret4"),
                    "ENV_NAME_2": URL("secret://test-cluster/otheruser/secret5"),
                    "ENV_NAME_3": URL("secret://othercluster/otheruser/secret6"),
                },
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = click.unstyle(JobStatusFormatter(uri_formatter=uri_fmtr)(description))
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Name: test-job-name\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: image:test-image:sometag\n"
            "Command: test-command\n"
            f"{resource}\n"
            "TTY: False\n"
            "Volumes:\n"
            "  /mnt/rw  storage:rw   \n"
            "Secret files:\n"
            "  /var/run/secret1  secret:secret1                         \n"
            "  /var/run/secret2  secret:/otheruser/secret2              \n"
            "  /var/run/secret3  secret://othercluster/otheruser/secret3\n"
            "Http URL: http://local.host.test/\n"
            "Http port: 80\n"
            "Http authentication: True\n"
            "Environment:\n"
            "  ENV_NAME_0=somevalue\n"
            "Secret environment:\n"
            "  ENV_NAME_1=secret:secret4\n"
            "  ENV_NAME_2=secret:/otheruser/secret5\n"
            "  ENV_NAME_3=secret://othercluster/otheruser/secret6\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 123\n"
            "=== Description ===\n"
            "ErrorDesc\n==================="
        )

    def test_job_with_working_dir(self) -> None:
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
                working_dir="/working/dir",
                resources=Resources(16, 0.1, 0, None, False, None, None),
                http=HTTPPort(port=80, requires_auth=True),
            ),
            ssh_server=URL("ssh-auth"),
            is_preemptible=False,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        status = click.unstyle(JobStatusFormatter(uri_formatter=uri_fmtr)(description))
        resource_formatter = ResourcesFormatter()
        resource = click.unstyle(resource_formatter(description.container.resources))
        assert (
            status == "Job: test-job\n"
            "Name: test-job-name\n"
            "Owner: test-user\n"
            "Cluster: default\n"
            "Description: test job description\n"
            "Status: failed (ErrorReason)\n"
            "Image: image:test-image:sometag\n"
            "Command: test-command\n"
            "Working dir: /working/dir\n"
            f"{resource}\n"
            "TTY: False\n"
            "Http URL: http://local.host.test/\n"
            "Http port: 80\n"
            "Http authentication: True\n"
            "Created: 2018-09-25T12:28:21.298672+00:00\n"
            "Started: 2018-09-25T12:28:59.759433+00:00\n"
            "Finished: 2018-09-25T12:28:59.759433+00:00\n"
            "Exit code: 123\n"
            "=== Description ===\n"
            "ErrorDesc\n==================="
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
            (JobStatus.CANCELLED, "Mar 04 2017"),
        ],
    )
    def test_status_date_relation(self, status: JobStatus, date: str) -> None:
        row = TabularJobRow.from_job(
            self._job_descr_with_status(status), "owner", image_formatter=str
        )
        assert click.unstyle(row.status) == f"{status}"
        assert row.when == date

    def test_image_from_registry_parsing_short(self) -> None:
        uri_fmtr = uri_formatter(username="bob", cluster_name="test-cluster")
        image_fmtr = image_formatter(uri_formatter=uri_fmtr)
        row = TabularJobRow.from_job(
            self._job_descr_with_status(
                JobStatus.PENDING,
                "registry-test.neu.ro/bob/swiss-box:red",
            ),
            "bob",
            image_formatter=image_fmtr,
        )
        assert row.image == "image:swiss-box:red"
        assert row.name == ""

    def test_image_from_registry_parsing_long(self) -> None:
        row = TabularJobRow.from_job(
            self._job_descr_with_status(
                JobStatus.PENDING,
                "registry-test.neu.ro/bob/swiss-box:red",
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
        result = [click.unstyle(item) for item in formatter([])]
        assert result == ["  ".join(self.columns)]

    def test_width_cutting(self) -> None:
        formatter = TabularJobsFormatter(
            10, "owner", parse_columns(None), image_formatter=str
        )
        result = [click.unstyle(item) for item in formatter([])]
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
        result = [click.unstyle(item.rstrip()) for item in formatter([job])]
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
        result = [click.unstyle(item.rstrip()) for item in formatter(jobs)]
        assert result == [
            f"ID                                        NAME   STATUS   WHEN         IMAGE                                     OWNER  CLUSTER  DESCRIPTION                           COMMAND",  # noqa: E501
            f"job-7ee153a7-249c-4be9-965a-ba3eafb67c82  name1  failed   Sep 25 2017  some-image-name:with-long-tag             {owner_printed}  default  some description long long long long  ls -la /some/path",  # noqa: E501
            f"job-7ee153a7-249c-4be9-965a-ba3eafb67c84  name2  pending  Sep 25 2017  image://test-cluster/bob/some-image-      {owner_printed}  default  some description                      ls -la /some/path",  # noqa: E501
            f"                                                                       name:with-long-tag",  # noqa: E501
        ]

    def test_custom_columns(self) -> None:
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
        result = [click.unstyle(item.rstrip()) for item in formatter([job])]

        assert result == ["         Status Code", "              failed"]

    def test_life_span(self) -> None:
        life_spans = [None, 0, 7 * 24 * 3600, 12345]
        jobs = [
            JobDescription(
                status=JobStatus.FAILED,
                id=f"job-{i}",
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
                life_span=life_span,
            )
            for i, life_span in enumerate(life_spans, 1)
        ]

        columns = parse_columns("id life_span")
        formatter = TabularJobsFormatter(100, "owner", columns, image_formatter=str)
        result = [click.unstyle(item.rstrip()) for item in formatter(jobs)]

        assert result == [
            "ID     LIFE-SPAN",
            "job-1",
            "job-2  no limit",
            "job-3  7d",
            "job-4  3h25m45s",
        ]

    def test_dates(self) -> None:
        items = [
            JobStatusHistory(
                status=JobStatus.PENDING,
                reason="ContainerCreating",
                description="",
                created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                started_at=None,
                finished_at=None,
            ),
            JobStatusHistory(
                status=JobStatus.RUNNING,
                reason="ContainerRunning",
                description="",
                created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                started_at=isoparse("2018-09-25T12:28:24.759433+00:00"),
                finished_at=None,
            ),
            JobStatusHistory(
                status=JobStatus.FAILED,
                reason="ErrorReason",
                description="ErrorDesc",
                created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                started_at=isoparse("2018-09-25T12:28:24.759433+00:00"),
                finished_at=isoparse("2018-09-26T12:28:59.759433+00:00"),
            ),
            JobStatusHistory(
                status=JobStatus.FAILED,
                reason="ErrorReason",
                description="ErrorDesc",
                created_at=datetime.now(timezone.utc) - timedelta(seconds=12345),
                started_at=datetime.now(timezone.utc) - timedelta(seconds=1234),
                finished_at=datetime.now(timezone.utc) - timedelta(seconds=12),
            ),
        ]
        jobs = [
            JobDescription(
                status=item.status,
                owner="test-user",
                cluster_name="default",
                id=f"job-{i}",
                uri=URL(f"job://default/test-user/job-{i}"),
                description=None,
                history=item,
                container=Container(
                    command="test-command",
                    image=RemoteImage.new_external_image(name="test-image"),
                    resources=Resources(16, 0.1, 0, None, False, None, None),
                ),
                ssh_server=URL("ssh-auth"),
                is_preemptible=False,
                internal_hostname="host.local",
            )
            for i, item in enumerate(items, 1)
        ]

        columns = parse_columns("id status when created started finished")
        formatter = TabularJobsFormatter(100, "test-user", columns, image_formatter=str)
        result = [click.unstyle(item.rstrip()) for item in formatter(jobs)]

        assert result == [
            "ID     STATUS   WHEN            CREATED      STARTED         FINISHED",
            "job-1  pending  Sep 25 2018     Sep 25 2018",
            "job-2  running  Sep 25 2018     Sep 25 2018  Sep 25 2018",
            "job-3  failed   Sep 26 2018     Sep 25 2018  Sep 25 2018     Sep 26 2018",
            "job-4  failed   12 seconds ago  3 hours ago  20 minutes ago  12 seconds ago",  # noqa: E501
        ]

    def test_working_dir(self) -> None:
        items = [None, "/working/dir"]
        jobs = [
            JobDescription(
                status=JobStatus.FAILED,
                owner="test-user",
                cluster_name="default",
                id=f"job-{i}",
                uri=URL(f"job://default/test-user/job-{i}"),
                description=None,
                history=JobStatusHistory(
                    status=JobStatus.FAILED,
                    reason="ErrorReason",
                    description="ErrorDesc",
                    created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                    started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                    finished_at=datetime.now(timezone.utc) - timedelta(seconds=1),
                ),
                container=Container(
                    command="test-command",
                    image=RemoteImage.new_external_image(name="test-image"),
                    resources=Resources(16, 0.1, 0, None, False, None, None),
                    working_dir=working_dir,
                ),
                ssh_server=URL("ssh-auth"),
                is_preemptible=False,
                internal_hostname="host.local",
            )
            for i, working_dir in enumerate(items, 1)
        ]

        columns = parse_columns("id workdir")
        formatter = TabularJobsFormatter(100, "test-user", columns, image_formatter=str)
        result = [click.unstyle(item.rstrip()) for item in formatter(jobs)]

        assert result == [
            "ID     WORKDIR",
            "job-1",
            "job-2  /working/dir",
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
        assert click.unstyle(resource_formatter(resources)) == (
            "Resources:\n" "  Memory: 16.0M\n" "  CPU: 0.1"
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
        assert click.unstyle(resource_formatter(resources)) == (
            "Resources:\n"
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
        assert click.unstyle(resource_formatter(resources)) == (
            "Resources:\n"
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
        assert click.unstyle(resource_formatter(resources=resources)) == (
            "Resources:\n"
            "  Memory: 16.0M\n"
            "  CPU: 0.1\n"
            "  TPU: v2-8/1.14\n"
            "  Additional: Extended SHM space"
        )
