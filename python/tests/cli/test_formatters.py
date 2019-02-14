import re
import textwrap
import time
from typing import Optional

import click
import pytest
from yarl import URL

from neuromation.cli.formatters import (
    ConfigFormatter,
    JobFormatter,
    JobListFormatter,
    JobStartProgress,
    JobStatusFormatter,
    JobTelemetryFormatter,
)
from neuromation.cli.formatters.abc import BaseFormatter
from neuromation.cli.formatters.jobs import ResourcesFormatter
from neuromation.cli.formatters.storage import (
    BSDAttributes,
    BSDPainter,
    FilesSorter,
    GnuIndicators,
    GnuPainter,
    LongFilesFormatter,
    NonePainter,
    PainterFactory,
    SimpleFilesFormatter,
    VerticalColumnsFilesFormatter,
)
from neuromation.cli.login import AuthToken
from neuromation.cli.rc import Config
from neuromation.client import (
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
            re.match(
                r"Status: pending \[\d+\.\d+ sec] \|",
                self.strip(progress(self.make_job(JobStatus.PENDING, None))),
            )
            is not None
        )
        assert (
            re.match(
                r"Status: pending ContainerCreating \[\d+\.\d+ sec] /",
                self.strip(
                    progress(self.make_job(JobStatus.PENDING, "ContainerCreating"))
                ),
            )
            is not None
        )
        assert (
            re.match(
                r"Status: pending ContainerCreating \[\d+\.\d+ sec] -",
                self.strip(
                    progress(self.make_job(JobStatus.PENDING, "ContainerCreating"))
                ),
            )
            is not None
        )
        assert (
            re.match(
                r"Status: succeeded \[\d+\.\d sec]",
                self.strip(
                    progress(self.make_job(JobStatus.SUCCEEDED, None), finish=True)
                ),
            )
            is not None
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

    def test_running_job(self) -> None:
        description = JobDescription(
            status=JobStatus.RUNNING,
            owner="test-user",
            id="test-job",
            description="test job description",
            history=JobStatusHistory(
                status=JobStatus.RUNNING,
                reason="ContainerRunning",
                description=None,
                created_at="2018-09-25T12:28:21.298672+00:00",
                started_at="2018-09-25T12:28:24.759433+00:00",
                finished_at=None,
            ),
            http_url=URL("http://local.host.test/"),
            ssh_server=URL("ssh://local.host.test:22/"),
            container=Container(
                command="test-command",
                image="test-image",
                resources=Resources.create(0.1, 0, None, None, False),
            ),
            ssh_auth_server="ssh-auth",
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


class TestNonePainter:
    def test_simple(self):
        painter = NonePainter()
        file = FileStatus(
            "File1",
            2048,
            FileStatusType.FILE,
            int(time.mktime(time.strptime("2018-01-01 03:00:00", "%Y-%m-%d %H:%M:%S"))),
            "read",
        )
        assert painter.paint(file.name, file) == file.name


class TestGnuPainter:
    def test_color_parsing_simple(self):
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
    def test_color_parsing_escaped_simple(self, escaped, result):
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
    def test_color_parsing_escaped_octal(self, escaped, result):
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
    def test_color_parsing_escaped_hex(self, escaped, result):
        painter = GnuPainter("rs=" + escaped)
        assert painter.color_indicator[GnuIndicators.RESET] == result

        painter = GnuPainter(escaped + "=1;2")
        assert painter.color_ext_type[result] == "1;2"

        painter = GnuPainter(escaped + "=" + escaped)
        assert painter.color_ext_type[result] == result

    def test_coloring(self):
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
        assert painter.paint(file.name, file) == "\x1b[0;44mtest.txt\x1b[0m"
        assert painter.paint(folder.name, folder) == "\x1b[32;41mtmp\x1b[0m"

        painter = GnuPainter("di=32;41:no=0;46")
        assert painter.paint(file.name, file) == "\x1b[0;46mtest.txt\x1b[0m"
        assert painter.paint(folder.name, folder) == "\x1b[32;41mtmp\x1b[0m"

        painter = GnuPainter("no=0;46")
        assert painter.paint(file.name, file) == "\x1b[0;46mtest.txt\x1b[0m"
        assert painter.paint(folder.name, folder) == "\x1b[01;34mtmp\x1b[0m"

        painter = GnuPainter("*.text=0;46")
        assert painter.paint(file.name, file) == "test.txt"
        assert painter.paint(folder.name, folder) == "\x1b[01;34mtmp\x1b[0m"

        painter = GnuPainter("*.txt=0;46")
        assert painter.paint(file.name, file) == "\x1b[0;46mtest.txt\x1b[0m"
        assert painter.paint(folder.name, folder) == "\x1b[01;34mtmp\x1b[0m"


class TestBSDPainter:
    def test_color_parsing(self):
        painter = BSDPainter("exfxcxdxbxegedabagacad")
        assert painter._colors[BSDAttributes.DIRECTORY] == "ex"

    def test_coloring(self):
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
        assert painter.paint(file.name, file) == "test.txt"
        assert painter.paint(folder.name, folder) == click.style("tmp", fg="blue")

        painter = BSDPainter("Eafxcxdxbxegedabagacad")
        assert painter.paint(file.name, file) == "test.txt"
        assert painter.paint(folder.name, folder) == click.style(
            "tmp", fg="blue", bg="black", bold=True
        )


class TestPainterFactory:
    def test_detection(self, monkeypatch):
        monkeypatch.setenv("LS_COLORS", "")
        monkeypatch.setenv("LSCOLORS", "")
        painter = PainterFactory.detect(True)
        assert isinstance(painter, NonePainter)

        monkeypatch.setenv("LSCOLORS", "exfxcxdxbxegedabagacad")
        monkeypatch.setenv("LS_COLORS", "di=32;41:fi=0;44:no=0;46")
        painter_without_color = PainterFactory.detect(False)
        painter_with_color = PainterFactory.detect(True)
        assert isinstance(painter_without_color, NonePainter)
        assert not isinstance(painter_with_color, NonePainter)

        monkeypatch.setenv("LSCOLORS", "")
        monkeypatch.setenv("LS_COLORS", "di=32;41:fi=0;44:no=0;46")
        painter = PainterFactory.detect(True)
        assert isinstance(painter, GnuPainter)

        monkeypatch.setenv("LSCOLORS", "exfxcxdxbxegedabagacad")
        monkeypatch.setenv("LS_COLORS", "")
        painter = PainterFactory.detect(True)
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

    def test_simple_formatter(self):
        formatter = SimpleFilesFormatter(color=False)
        assert list(formatter(self.files_and_folders)) == [
            f"{file.name}" for file in self.files_and_folders
        ]

    def test_long_formatter(self):
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

    def test_column_formatter(self):
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
            url="https://dev.url/api/v1",
            registry_url="https://registry-dev.url/api/v1",
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
              API URL: https://dev.url/api/v1
              Docker Registry URL: https://registry-dev.url/api/v1
              Github RSA Path: path"""
        )
