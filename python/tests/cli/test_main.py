from unittest.mock import MagicMock, patch

import pytest

import neuromation
from neuromation.cli import rc
from neuromation.cli.commands import dispatch
from neuromation.cli.main import neuro
from neuromation.client import FileStatus
from neuromation.client.jobs import JobItem
from tests.utils import mocked_async_context_manager


@pytest.fixture
def dispatch_mocked(mocked_jobs):
    config = rc.ConfigFactory.load()
    format_spec = {"api_url": config.url, "username": "test-user"}

    def _dispatch(args):
        return dispatch(
            target=neuro, tail=args, format_spec=format_spec, token=config.auth
        )

    return _dispatch


class TestNeuroStoreLs:
    @patch(
        "neuromation.cli.command_handlers.PlatformListDirOperation.ls",
        new=lambda *args: [
            FileStatus("file1", 11, "FILE", 2018, "read"),
            FileStatus("file2", 12, "FILE", 2018, "write"),
            FileStatus("dir1", 0, "DIRECTORY", 2018, "manage"),
        ],
    )
    def test_neuro_store_ls__normal(self, dispatch_mocked):
        res = dispatch_mocked(["store", "ls", "storage://~/"])
        expected = (
            "file           11             file1\n"
            + "file           12             file2\n"
            + "directory      0              dir1"
        )
        assert res == expected

    @patch(
        "neuromation.cli.command_handlers.PlatformListDirOperation.ls",
        new=lambda *args: [],
    )
    def test_neuro_store_ls__empty(self, dispatch_mocked):
        res = dispatch_mocked(["store", "ls", "storage://~/"])
        assert res == ""


class TestNeuroJobLs:
    def _job_submit_output(self, job_id):
        return (
            f"Job ID: {job_id} Status: pending\n"
            + "Shortcuts:\n"
            + f"  neuro job status {job_id}  # check job status\n"
            + f"  neuro job monitor {job_id} # monitor job stdout\n"
            + f"  neuro job kill {job_id}    # kill job"
        )

    @patch(
        "neuromation.cli.command_handlers.JobHandlerOperations.submit",
        new=lambda *args: JobItem(
            status="pending", id="job-id", client=None, url="url"
        ),
    )
    def test_neuro_job_submit__lack_preemptible_options(self, dispatch_mocked):
        res = dispatch_mocked(["job", "submit", "ubuntu"])
        assert res == self._job_submit_output("job-id")

    @patch(
        "neuromation.cli.command_handlers.JobHandlerOperations.submit",
        new=lambda *args: JobItem(
            status="pending", id="job-id", client=None, url="url"
        ),
    )
    def test_neuro_job_submit__preemptible(self, dispatch_mocked):
        res = dispatch_mocked(["job", "submit", "ubuntu", "--preemptible"])
        assert res == self._job_submit_output("job-id")

    @patch(
        "neuromation.cli.command_handlers.JobHandlerOperations.submit",
        new=lambda *args: JobItem(
            status="pending", id="job-id", client=None, url="url"
        ),
    )
    def test_neuro_job_submit__non_preemptible(self, dispatch_mocked):
        res = dispatch_mocked(["job", "submit", "ubuntu", "--non-preemptible"])
        assert res == self._job_submit_output("job-id")

    @patch(
        "neuromation.cli.command_handlers.JobHandlerOperations.submit",
        new=lambda *args: JobItem(
            status="pending", id="job-id", client=None, url="url"
        ),
    )
    def test_neuro_job_submit__both_preemptible_and_non_preemptible(
        self, dispatch_mocked
    ):
        with pytest.raises(neuromation.client.IllegalArgumentError):
            dispatch_mocked(
                ["job", "submit", "ubuntu", "--preemptible", "--non-preemptible"]
            )


# TODO: A Yushkovskiy 4.12.2018: add tests on "job monitor", "job kill" and other
# ... sub-methods of 'main()' that contain logic
