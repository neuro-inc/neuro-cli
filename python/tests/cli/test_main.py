from unittest.mock import patch

import pytest

import neuromation
from neuromation.cli import rc
from neuromation.cli.commands import dispatch
from neuromation.cli.main import neuro
from neuromation.client import FileStatus
from neuromation.client.jobs import JobItem


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
