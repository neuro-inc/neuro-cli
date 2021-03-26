import io
import itertools
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

import pytest
from dateutil.parser import isoparse
from rich.console import Console
from rich.text import Text
from yarl import URL

from neuro_sdk import (
    Container,
    DiskVolume,
    HTTPPort,
    JobDescription,
    JobRestartPolicy,
    JobStatus,
    JobStatusHistory,
    JobTelemetry,
    RemoteImage,
    Resources,
    SecretFile,
    Volume,
)
from neuro_sdk.jobs import JobStatusItem
from neuro_sdk.parsing_utils import _ImageNameParser

from neuro_cli.formatters.jobs import (
    JobStartProgress,
    JobStatusFormatter,
    JobTelemetryFormatter,
    LifeSpanUpdateFormatter,
    SimpleJobsFormatter,
    TabularJobRow,
    TabularJobsFormatter,
    format_timedelta,
)
from neuro_cli.formatters.utils import (
    DatetimeFormatter,
    format_datetime_human,
    format_datetime_iso,
    image_formatter,
    uri_formatter,
)
from neuro_cli.parse_utils import parse_ps_columns, parse_sort_keys, parse_top_columns

TEST_JOB_ID = "job-ad09fe07-0c64-4d32-b477-3b737d215621"
TEST_JOB_ID2 = "job-3f9c5f93-45be-4c5d-acbd-11c68260235f"
TEST_JOB_NAME = "test-job-name"

_NewConsole = Callable[..., Console]


def _format_datetime_human(when: Optional[datetime], precise: bool = False) -> str:
    return format_datetime_human(when, precise=precise, timezone=timezone.utc)


@pytest.fixture(params=["iso", "human"])
def datetime_formatter(request: Any) -> DatetimeFormatter:
    if request.param == "iso":
        return format_datetime_iso
    if request.param == "human":
        return _format_datetime_human
    raise Exception(f"Unknown format mode {request.param}.")


@pytest.fixture
def new_console() -> _NewConsole:
    def factory(*, tty: bool, color: bool = True) -> Console:
        file = io.StringIO()
        # console doesn't accept the time source,
        # using the real time in tests is not reliable
        return Console(
            file=file,
            width=160,
            height=24,
            force_terminal=tty,
            color_system="auto" if color else None,
            record=True,
            highlighter=None,
            legacy_windows=False,
            log_path=False,
            log_time=False,
        )

    return factory


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
        scheduler_enabled=True,
        pass_config=True,
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
        scheduler_enabled=True,
        pass_config=True,
    )


class TestJobStartProgress:
    def make_job(
        self,
        status: JobStatus,
        reason: str,
        *,
        name: Optional[str] = None,
        life_span: Optional[float] = None,
        description: str = "ErrorDesc",
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
                description=description,
                created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                finished_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
            ),
            container=Container(
                command="test-command",
                image=RemoteImage.new_external_image(name="test-image"),
                resources=Resources(
                    16,
                    0.1,
                    4,
                    "nvidia-tesla-p4",
                    True,
                    tpu_type="v2-8",
                    tpu_software_version="1.14",
                ),
            ),
            scheduler_enabled=False,
            pass_config=True,
            life_span=life_span,
        )

    def test_quiet(self, rich_cmp: Any, new_console: _NewConsole) -> None:
        job = self.make_job(JobStatus.PENDING, "")
        console = new_console(tty=True, color=True)
        with JobStartProgress.create(console, quiet=True) as progress:
            progress.begin(job)
            rich_cmp(console, index=0)
            progress.step(job)
            rich_cmp(console, index=1)
            progress.end(job)
            rich_cmp(console, index=2)

    def test_no_tty_begin(self, rich_cmp: Any, new_console: _NewConsole) -> None:
        console = new_console(tty=False, color=True)
        with JobStartProgress.create(console, quiet=False) as progress:
            progress.begin(self.make_job(JobStatus.PENDING, ""))
            rich_cmp(console)

    def test_no_tty_begin_with_name(
        self, rich_cmp: Any, new_console: _NewConsole
    ) -> None:
        console = new_console(tty=False, color=True)
        with JobStartProgress.create(console, quiet=False) as progress:
            progress.begin(self.make_job(JobStatus.PENDING, "", name="job-name"))
            rich_cmp(console)

    def test_no_tty_step(self, rich_cmp: Any, new_console: _NewConsole) -> None:
        console = new_console(tty=False, color=True)
        with JobStartProgress.create(console, quiet=False) as progress:
            progress.step(self.make_job(JobStatus.PENDING, ""))
            progress.step(self.make_job(JobStatus.PENDING, ""))
            progress.step(self.make_job(JobStatus.RUNNING, "reason"))
            rich_cmp(console)

    def test_no_tty_end(self, rich_cmp: Any, new_console: _NewConsole) -> None:
        console = new_console(tty=False, color=True)
        with JobStartProgress.create(console, quiet=False) as progress:
            progress.end(self.make_job(JobStatus.RUNNING, ""))
            rich_cmp(console)

    def test_tty_begin(self, rich_cmp: Any, new_console: _NewConsole) -> None:
        console = new_console(tty=True, color=True)
        with JobStartProgress.create(console, quiet=False) as progress:
            progress.begin(self.make_job(JobStatus.PENDING, ""))
            rich_cmp(console)

    def test_tty_begin_with_name(self, rich_cmp: Any, new_console: _NewConsole) -> None:
        console = new_console(tty=True, color=True)
        with JobStartProgress.create(console, quiet=False) as progress:
            progress.begin(self.make_job(JobStatus.PENDING, "", name="job-name"))
            rich_cmp(console)

    @pytest.mark.skipif(
        sys.platform == "win32", reason="On Windows spinner uses another characters set"
    )
    def test_tty_step(
        self, rich_cmp: Any, new_console: _NewConsole, monkeypatch: Any
    ) -> None:
        monkeypatch.setattr(
            JobStartProgress, "time_factory", itertools.count(10).__next__
        )
        console = new_console(tty=True, color=True)
        with JobStartProgress.create(console, quiet=False) as progress:
            progress.step(self.make_job(JobStatus.PENDING, "Pulling", description=""))
            progress.step(self.make_job(JobStatus.PENDING, "Pulling", description=""))
            progress.step(self.make_job(JobStatus.RUNNING, "reason", description=""))
            rich_cmp(console)

    def test_tty_end(self, rich_cmp: Any, new_console: _NewConsole) -> None:
        console = new_console(tty=True, color=True)
        with JobStartProgress.create(console, quiet=False) as progress:
            progress.end(self.make_job(JobStatus.RUNNING, ""))
            rich_cmp(console)

    def test_tty_end_with_life_span(
        self, rich_cmp: Any, new_console: _NewConsole
    ) -> None:
        console = new_console(tty=True, color=True)
        with JobStartProgress.create(console, quiet=False) as progress:
            progress.end(self.make_job(JobStatus.RUNNING, "", life_span=24 * 3600))


class TestJobOutputFormatter:
    def test_job_with_name(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=False,
            pass_config=True,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_job_with_tags(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=False,
            pass_config=True,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_job_with_tags_wrap_tags(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=False,
            pass_config=True,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_job_with_life_span_with_value(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=False,
            pass_config=True,
            life_span=1.0 * ((60 * 60 * 24 * 1) + (60 * 60 * 2) + (60 * 3) + 4),
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_job_with_life_span_without_value(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=False,
            pass_config=True,
            life_span=0.0,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_job_with_restart_policy(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
                restarts=4,
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
            scheduler_enabled=False,
            pass_config=True,
            restart_policy=JobRestartPolicy.ALWAYS,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_pending_job(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=False,
            pass_config=True,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_pending_job_no_reason(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=True,
            pass_config=True,
            owner="owner",
            cluster_name="default",
            uri=URL("job://default/owner/test-job"),
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_pending_job_with_reason(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=True,
            pass_config=True,
            owner="owner",
            cluster_name="default",
            uri=URL("job://default/owner/test-job"),
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_pending_job_no_description(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=True,
            pass_config=True,
            owner="owner",
            cluster_name="default",
            uri=URL("job://default/owner/test-job"),
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_running_job(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=False,
            pass_config=True,
            internal_hostname="host.local",
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_running_job_with_status_items(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
                transitions=[
                    JobStatusItem(
                        status=JobStatus.PENDING,
                        transition_time=isoparse("2018-09-25T12:28:21.298672+00:00"),
                        reason="Creating",
                    ),
                    JobStatusItem(
                        status=JobStatus.PENDING,
                        transition_time=isoparse("2018-09-25T12:28:22.298672+00:00"),
                        reason="Scheduling",
                    ),
                    JobStatusItem(
                        status=JobStatus.PENDING,
                        transition_time=isoparse("2018-09-25T12:28:23.298672+00:00"),
                        reason="ContainerCreating",
                    ),
                    JobStatusItem(
                        status=JobStatus.RUNNING,
                        transition_time=isoparse("2018-09-25T12:28:24.759433+00:00"),
                    ),
                ],
            ),
            http_url=URL("http://local.host.test/"),
            container=Container(
                command="test-command",
                image=RemoteImage.new_external_image(name="test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
            ),
            scheduler_enabled=False,
            pass_config=True,
            internal_hostname="host.local",
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_running_named_job(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=False,
            pass_config=True,
            internal_hostname="host.local",
            internal_hostname_named="test-job--test-owner.local",
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_job_with_entrypoint(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=False,
            pass_config=True,
            internal_hostname="host.local",
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_job_with_environment(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=False,
            pass_config=True,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_job_with_volumes_short(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=False,
            pass_config=True,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_job_with_volumes_long(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=False,
            pass_config=True,
        )

        rich_cmp(
            JobStatusFormatter(
                uri_formatter=str, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_job_with_secrets_short(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=False,
            pass_config=True,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_job_with_disk_volumes_short(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
                disk_volumes=[
                    DiskVolume(
                        URL("disk://test-cluster/test-user/disk1"),
                        "/mnt/disk1",
                        read_only=True,
                    ),
                    DiskVolume(
                        URL("disk://test-cluster/otheruser/disk2"),
                        "/mnt/disk2",
                        read_only=False,
                    ),
                    DiskVolume(
                        URL("disk://othercluster/otheruser/disk3"),
                        "/mnt/disk3",
                        read_only=False,
                    ),
                ],
            ),
            scheduler_enabled=False,
            pass_config=True,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_job_with_working_dir(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=False,
            pass_config=True,
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_job_with_preset_name(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            preset_name="cpu-small",
            container=Container(
                command="test-command",
                image=RemoteImage.new_external_image(name="test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
            ),
            scheduler_enabled=False,
            pass_config=True,
            owner="owner",
            cluster_name="default",
            uri=URL("job://default/owner/test-job"),
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )

    def test_job_on_preemptible_node(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=True,
            preemptible_node=True,
            pass_config=True,
            owner="owner",
            cluster_name="default",
            uri=URL("job://default/owner/test-job"),
        )

        uri_fmtr = uri_formatter(username="test-user", cluster_name="test-cluster")
        rich_cmp(
            JobStatusFormatter(
                uri_formatter=uri_fmtr, datetime_formatter=datetime_formatter
            )(description)
        )


class TestJobTelemetryFormatter:
    # Use utc timezone in test for stable constant result

    def test_format_telemetry_no_gpu(
        self,
        job_descr: JobDescription,
        rich_cmp: Any,
        new_console: _NewConsole,
        datetime_formatter: DatetimeFormatter,
    ) -> None:
        console = new_console(tty=True, color=True)
        with JobTelemetryFormatter(
            console,
            "owner",
            [],
            parse_top_columns(None),
            image_formatter=str,
            datetime_formatter=datetime_formatter,
        ) as fmt:
            timestamp = 1_517_248_466.238_723_6
            telemetry = JobTelemetry(cpu=0.12345, memory=256.123, timestamp=timestamp)
            # Use utc timezone in test for stable constant result
            fmt.update(job_descr, telemetry)
            assert fmt.changed
            fmt.render()
            assert not fmt.changed
            rich_cmp(console)

    def test_format_telemetry_seq(
        self,
        job_descr: JobDescription,
        rich_cmp: Any,
        new_console: _NewConsole,
        datetime_formatter: DatetimeFormatter,
    ) -> None:
        console = new_console(tty=True, color=True)
        with JobTelemetryFormatter(
            console,
            "owner",
            parse_sort_keys("cpu"),
            parse_top_columns(None),
            image_formatter=str,
            datetime_formatter=datetime_formatter,
        ) as fmt:
            timestamp = 1_517_248_466.238_723_6
            telemetry = JobTelemetry(cpu=0.12345, memory=256.123, timestamp=timestamp)
            fmt.update(job_descr, telemetry)
            assert fmt.changed
            fmt.render()
            assert not fmt.changed
            rich_cmp(console, index=0)

            timestamp = 1_517_248_467.238_723_6
            telemetry = JobTelemetry(cpu=0.23456, memory=128.123, timestamp=timestamp)
            fmt.update(job_descr, telemetry)
            assert fmt.changed
            fmt.render()
            assert not fmt.changed
            rich_cmp(console, index=1)

    def test_format_telemetry_multiple_jobs(
        self,
        job_descr: JobDescription,
        rich_cmp: Any,
        new_console: _NewConsole,
        datetime_formatter: DatetimeFormatter,
    ) -> None:
        job_descr2 = replace(job_descr, id=TEST_JOB_ID2)
        console = new_console(tty=True, color=True)
        with JobTelemetryFormatter(
            console,
            "owner",
            parse_sort_keys("cpu"),
            parse_top_columns(None),
            image_formatter=str,
            datetime_formatter=datetime_formatter,
        ) as fmt:
            timestamp = 1_517_248_466.238_723_6
            telemetry = JobTelemetry(cpu=0.12345, memory=256.123, timestamp=timestamp)
            fmt.update(job_descr, telemetry)
            assert fmt.changed
            fmt.render()
            assert not fmt.changed
            rich_cmp(console, index=0)

            timestamp = 1_517_248_467.238_723_6
            telemetry = JobTelemetry(cpu=0.23456, memory=128.123, timestamp=timestamp)
            fmt.update(job_descr2, telemetry)
            assert fmt.changed
            fmt.render()
            assert not fmt.changed
            rich_cmp(console, index=1)

            fmt.sort_keys = parse_sort_keys("owner,memory")
            fmt.render()
            assert not fmt.changed
            rich_cmp(console, index=3)

            fmt.sort_keys = parse_sort_keys("owner,-memory")
            fmt.render()
            assert not fmt.changed
            rich_cmp(console, index=4)

            fmt.remove(job_descr2.id)
            assert fmt.changed
            fmt.render()
            assert not fmt.changed
            rich_cmp(console, index=2)

    def test_format_telemetry_limited_height(
        self,
        job_descr: JobDescription,
        rich_cmp: Any,
        new_console: _NewConsole,
        datetime_formatter: DatetimeFormatter,
    ) -> None:
        job_descr2 = replace(job_descr, id=TEST_JOB_ID2)
        console = new_console(tty=True, color=True)
        with JobTelemetryFormatter(
            console,
            "owner",
            parse_sort_keys("cpu"),
            parse_top_columns(None),
            image_formatter=str,
            datetime_formatter=datetime_formatter,
            maxrows=1,
        ) as fmt:
            timestamp = 1_517_248_466.238_723_6
            telemetry = JobTelemetry(cpu=0.12345, memory=256.123, timestamp=timestamp)
            fmt.update(job_descr, telemetry)
            assert fmt.changed
            fmt.render()
            assert not fmt.changed
            rich_cmp(console, index=0)

            timestamp = 1_517_248_467.238_723_6
            telemetry = JobTelemetry(cpu=0.23456, memory=128.123, timestamp=timestamp)
            fmt.update(job_descr2, telemetry)
            assert fmt.changed
            fmt.render()
            assert not fmt.changed
            rich_cmp(console, index=1)

    def test_format_telemetry_with_gpu(
        self,
        job_descr: JobDescription,
        rich_cmp: Any,
        new_console: _NewConsole,
        datetime_formatter: DatetimeFormatter,
    ) -> None:
        console = new_console(tty=True, color=True)
        with JobTelemetryFormatter(
            console,
            "owner",
            [],
            parse_top_columns(None),
            image_formatter=str,
            datetime_formatter=datetime_formatter,
        ) as fmt:
            timestamp = 1_517_248_466
            telemetry = JobTelemetry(
                cpu=0.12345,
                memory=256.1234,
                timestamp=timestamp,
                gpu_duty_cycle=99,
                gpu_memory=64.5,
            )
            fmt.update(job_descr, telemetry)
            assert fmt.changed
            fmt.render()
            assert not fmt.changed
            rich_cmp(console)


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
    def test_empty(self, rich_cmp: Any) -> None:
        formatter = SimpleJobsFormatter()
        rich_cmp(formatter([]))

    def test_list(self, rich_cmp: Any) -> None:
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
                scheduler_enabled=True,
                pass_config=True,
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
                scheduler_enabled=True,
                pass_config=True,
            ),
        ]
        formatter = SimpleJobsFormatter()
        rich_cmp(formatter(jobs))


class TestTabularJobRow:
    image_parser = _ImageNameParser(
        "bob", "test-cluster", {"test-cluster": URL("https://registry-test.neu.ro")}
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
            scheduler_enabled=True,
            pass_config=True,
        )

    def test_with_job_name(self, datetime_formatter: DatetimeFormatter) -> None:
        row = TabularJobRow.from_job(
            self._job_descr_with_status(JobStatus.RUNNING, name="job-name"),
            "owner",
            image_formatter=str,
            datetime_formatter=datetime_formatter,
        )
        assert row.name == "job-name"

    def test_without_job_name(self, datetime_formatter: DatetimeFormatter) -> None:
        row = TabularJobRow.from_job(
            self._job_descr_with_status(JobStatus.RUNNING, name=None),
            "owner",
            image_formatter=str,
            datetime_formatter=datetime_formatter,
        )
        assert row.name == ""

    @pytest.mark.parametrize(
        "status,date,color",
        [
            (JobStatus.PENDING, "Jan 02 2017", "cyan"),
            (JobStatus.RUNNING, "Feb 03 2017", "blue"),
            (JobStatus.FAILED, "Mar 04 2017", "red"),
            (JobStatus.SUCCEEDED, "Mar 04 2017", "green"),
            (JobStatus.CANCELLED, "Mar 04 2017", "yellow"),
        ],
    )
    def test_status_date_relation(
        self,
        status: JobStatus,
        date: str,
        color: str,
    ) -> None:
        row = TabularJobRow.from_job(
            self._job_descr_with_status(status),
            "owner",
            image_formatter=str,
            datetime_formatter=format_datetime_human,
        )
        assert row.status == Text(status, style="color")
        assert row.when == date

    def test_image_from_registry_parsing_short(
        self, datetime_formatter: DatetimeFormatter
    ) -> None:
        uri_fmtr = uri_formatter(username="bob", cluster_name="test-cluster")
        image_fmtr = image_formatter(uri_formatter=uri_fmtr)
        row = TabularJobRow.from_job(
            self._job_descr_with_status(
                JobStatus.PENDING,
                "registry-test.neu.ro/bob/swiss-box:red",
            ),
            "bob",
            image_formatter=image_fmtr,
            datetime_formatter=datetime_formatter,
        )
        assert row.image == "image:swiss-box:red"
        assert row.name == ""

    def test_image_from_registry_parsing_long(
        self, datetime_formatter: DatetimeFormatter
    ) -> None:
        row = TabularJobRow.from_job(
            self._job_descr_with_status(
                JobStatus.PENDING,
                "registry-test.neu.ro/bob/swiss-box:red",
            ),
            "owner",
            image_formatter=str,
            datetime_formatter=datetime_formatter,
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
        "bob", "test-cluster", {"test-cluster": URL("https://registry-test.neu.ro")}
    )

    def test_empty(self, rich_cmp: Any, datetime_formatter: DatetimeFormatter) -> None:
        formatter = TabularJobsFormatter(
            "owner",
            parse_ps_columns(None),
            image_formatter=str,
            datetime_formatter=datetime_formatter,
        )
        rich_cmp(formatter([]))

    @pytest.mark.parametrize(
        "idx,owner_name,owner_printed", [(0, "owner", "<you>"), (1, "alice", "alice")]
    )
    def test_short_cells(
        self,
        idx: int,
        owner_name: str,
        owner_printed: str,
        rich_cmp: Any,
    ) -> None:
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
            scheduler_enabled=True,
            pass_config=True,
        )
        formatter = TabularJobsFormatter(
            "owner",
            parse_ps_columns(None),
            image_formatter=str,
            datetime_formatter=format_datetime_human,
        )
        rich_cmp(formatter([job]), index=idx)

    @pytest.mark.parametrize(
        "idx,owner_name,owner_printed", [(0, "owner", "<you>"), (1, "alice", "alice")]
    )
    def test_wide_cells(
        self,
        idx: int,
        owner_name: str,
        owner_printed: str,
        rich_cmp: Any,
        datetime_formatter: DatetimeFormatter,
    ) -> None:
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
                scheduler_enabled=True,
                pass_config=True,
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
                scheduler_enabled=True,
                pass_config=True,
            ),
        ]
        formatter = TabularJobsFormatter(
            "owner",
            parse_ps_columns(None),
            image_formatter=str,
            datetime_formatter=datetime_formatter,
        )
        rich_cmp(formatter(jobs), index=idx)

    def test_custom_columns(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
            scheduler_enabled=True,
            pass_config=True,
        )

        columns = parse_ps_columns("{status;align=right;min=20;Status Code}")
        formatter = TabularJobsFormatter(
            "owner",
            columns,
            image_formatter=str,
            datetime_formatter=datetime_formatter,
        )
        rich_cmp(formatter([job]))

    def test_life_span(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
                scheduler_enabled=True,
                pass_config=True,
                life_span=life_span,
            )
            for i, life_span in enumerate(life_spans, 1)
        ]

        columns = parse_ps_columns("id life_span")
        formatter = TabularJobsFormatter(
            "owner",
            columns,
            image_formatter=str,
            datetime_formatter=datetime_formatter,
        )
        rich_cmp(formatter(jobs))

    def test_dates(self, rich_cmp: Any) -> None:
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
                scheduler_enabled=False,
                pass_config=True,
                internal_hostname="host.local",
            )
            for i, item in enumerate(items, 1)
        ]

        columns = parse_ps_columns("id status when created started finished")
        formatter = TabularJobsFormatter(
            "test-user",
            columns,
            image_formatter=str,
            datetime_formatter=format_datetime_human,
        )
        rich_cmp(formatter(jobs))

    def test_working_dir(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
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
                scheduler_enabled=False,
                pass_config=True,
                internal_hostname="host.local",
            )
            for i, working_dir in enumerate(items, 1)
        ]

        columns = parse_ps_columns("id workdir")
        formatter = TabularJobsFormatter(
            "test-user",
            columns,
            image_formatter=str,
            datetime_formatter=datetime_formatter,
        )
        rich_cmp(formatter(jobs))

    def test_preset(self, rich_cmp: Any, datetime_formatter: DatetimeFormatter) -> None:
        items = [None, "cpu-small", "gpu-large"]
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
                ),
                scheduler_enabled=False,
                pass_config=True,
                internal_hostname="host.local",
                preset_name=preset_name,
            )
            for i, preset_name in enumerate(items, 1)
        ]

        columns = parse_ps_columns("id preset")
        formatter = TabularJobsFormatter(
            "test-user",
            columns,
            image_formatter=str,
            datetime_formatter=datetime_formatter,
        )
        rich_cmp(formatter(jobs))


class TestLifeSpanUpdateFormatter:
    async def test_not_finished(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
        job = JobDescription(
            status=JobStatus.RUNNING,
            owner="test-user",
            cluster_name="default",
            id=f"job-id",
            uri=URL(f"job://default/test-user/job-id"),
            description=None,
            history=JobStatusHistory(
                status=JobStatus.RUNNING,
                reason="ErrorReason",
                description="ErrorDesc",
                created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
                started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
                finished_at=datetime.now(timezone.utc) - timedelta(seconds=1),
                transitions=[
                    JobStatusItem(
                        status=JobStatus.PENDING,
                        transition_time=isoparse("2018-09-25T12:28:21.298672+00:00"),
                        reason="Creating",
                    ),
                    JobStatusItem(
                        status=JobStatus.PENDING,
                        transition_time=isoparse("2018-09-25T12:28:22.298672+00:00"),
                        reason="Scheduling",
                    ),
                    JobStatusItem(
                        status=JobStatus.PENDING,
                        transition_time=isoparse("2018-09-25T12:28:23.298672+00:00"),
                        reason="ContainerCreating",
                    ),
                    JobStatusItem(
                        status=JobStatus.RUNNING,
                        transition_time=isoparse("2018-09-25T12:28:24.759433+00:00"),
                    ),
                ],
            ),
            container=Container(
                command="test-command",
                image=RemoteImage.new_external_image(name="test-image"),
                resources=Resources(16, 0.1, 0, None, False, None, None),
            ),
            scheduler_enabled=False,
            pass_config=True,
        )

        formatter = LifeSpanUpdateFormatter(
            datetime_formatter=datetime_formatter,
        )
        rich_cmp(formatter(job))

    async def test_finished(
        self, rich_cmp: Any, datetime_formatter: DatetimeFormatter
    ) -> None:
        job = JobDescription(
            status=JobStatus.SUCCEEDED,
            owner="test-user",
            cluster_name="default",
            id=f"job-id",
            uri=URL(f"job://default/test-user/job-id"),
            description=None,
            history=JobStatusHistory(
                status=JobStatus.SUCCEEDED,
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
            ),
            scheduler_enabled=False,
            pass_config=True,
            life_span=3600,
        )

        formatter = LifeSpanUpdateFormatter(
            datetime_formatter=datetime_formatter,
        )
        rich_cmp(formatter(job))
