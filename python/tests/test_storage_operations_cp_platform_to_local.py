import os
from pathlib import PurePath
from typing import Callable, Dict, List
from unittest.mock import Mock
from urllib.parse import urlparse

import pytest

from neuromation.cli.command_handlers import CopyOperation, NonRecursivePlatformToLocal
from neuromation.client import FileStatus, ResourceNotFound


def _os_exists(tree: Dict) -> Callable:
    def check(src: str):
        root = tree
        parts = src.split("/")
        for part in parts:
            if not part:
                continue
            if part in root["c"]:
                root = root["c"][part]
            else:
                return False
        return True

    return check


def _os_isdir(tree: Dict) -> Callable:
    def check(src: str):
        root = tree
        parts = src.split("/")
        for part in parts:
            if not part:
                continue
            if part in root["c"]:
                root = root["c"][part]
            else:
                return False
        return root["_dir"]

    return check


def _platform_ls(dirs: List) -> Callable:
    def ls(path: str):
        coll = [v["files"] for v in dirs if v["path"] == path]
        return coll[0]

    return ls


def _platform_stat(dirs: List) -> Callable:
    def stat(path: str):
        try:
            item = next(v for v in dirs if v["path"] == path)
            return FileStatus(
                path=item["path"],
                size=0,
                type="DIRECTORY",
                modification_time=0,
                permission="",
            )
        except StopIteration:
            path_ = PurePath(path).parent
            name_ = PurePath(path).name
            try:
                item = next(v for v in dirs if v["path"] == str(path_))
                item = next(v for v in item.get("files") if v.path == name_)
                return item
            except StopIteration:
                raise ResourceNotFound()

    return stat


local_tree = {
    "c": {
        "localdir": {
            "c": {
                "dir": {
                    "c": {"platform_existing": {"c": {}, "_dir": True}},
                    "_dir": True,
                },
                "abc.txt": {"_dir": False},
            },
            "_dir": True,
        }
    },
    "_dir": True,
}

platform_tree = [
    {
        "path": "/",
        "files": [
            FileStatus("/alice", 0, "DIRECTORY", 0, "read"),
            FileStatus("/bob", 0, "DIRECTORY", 0, "read"),
        ],
    },
    {
        "path": "/alice",
        "files": [FileStatus("platform_existing", 0, "DIRECTORY", 0, "read")],
    },
    {
        "path": "/alice/platform_existing",
        "files": [
            FileStatus("my_file.txt", 100, "FILE", 0, "read"),
            FileStatus("dir", 0, "DIRECTORY", 0, "read"),
            FileStatus("di1", 0, "DIRECTORY", 0, "read"),
        ],
    },
    {
        "path": "/alice/platform_existing/dir",
        "files": [FileStatus("my_file2.txt", 100, "FILE", 0, "read")],
    },
    {"path": "/alice/platform_existing/di1", "files": []},
    {"path": "/bob", "files": [FileStatus("bob_data", 0, "DIRECTORY", 0, "read")]},
    {
        "path": "/bob/bob_data",
        "files": [FileStatus("file.model", 120, "FILE", 0, "read")],
    },
]


class TestCopyRecursivePlatformToLocal:
    def _structure(self, mocked_store, monkeypatch, mkdir_mock=Mock()):
        monkeypatch.setattr(os.path, "exists", _os_exists(local_tree))
        monkeypatch.setattr(os.path, "isdir", _os_isdir(local_tree))
        monkeypatch.setattr(os, "mkdir", mkdir_mock)
        mocked_store.ls = _platform_ls(platform_tree)
        mocked_store.stats = _platform_stat(platform_tree)

    def test_source_file(self, mocked_store, partial_mocked_store, monkeypatch):
        # TODO should fallback to file copy
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "storage", "file", True)
        NonRecursivePlatformToLocal.copy_file = transfer_mock
        op.copy(
            urlparse("storage:///platform_existing/my_file.txt"),
            urlparse("file:///localdir/dir/"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1

    def test_ok(self, mocked_store, partial_mocked_store, monkeypatch):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "storage", "file", True)
        op.copy_file = transfer_mock
        op.copy(
            urlparse("storage:///platform_existing/"),
            urlparse("file:///localdir/dir/"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 2
        transfer_mock.assert_any_call(
            "/alice/platform_existing/my_file.txt",
            "/localdir/dir/platform_existing/my_file.txt",
            FileStatus("my_file.txt", 100, "FILE", 0, "read"),
            partial_mocked_store,
        )
        transfer_mock.assert_any_call(
            "/alice/platform_existing/dir/my_file2.txt",
            "/localdir/dir/platform_existing/dir/my_file2.txt",
            FileStatus("my_file2.txt", 100, "FILE", 0, "read"),
            partial_mocked_store,
        )

    def test_cannot_create_dir(self, mocked_store, partial_mocked_store, monkeypatch):
        mkdir_mock = Mock()
        transfer_mock = Mock()

        self._structure(mocked_store, monkeypatch, mkdir_mock)

        op = CopyOperation.create("alice", "storage", "file", True)
        op.copy_file = transfer_mock
        with pytest.raises(NotADirectoryError):
            op.copy(
                urlparse("storage:///platform_existing/"),
                urlparse("file:///localdir/"),
                partial_mocked_store,
            )

        assert mkdir_mock.call_count == 1
        assert transfer_mock.call_count == 0

    def test_ok_copy_bob_data(self, mocked_store, partial_mocked_store, monkeypatch):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "storage", "file", True)
        op.copy_file = transfer_mock
        op.copy(
            urlparse("storage://bob/"),
            urlparse("file:///localdir/dir/"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/bob/bob_data/file.model",
            "/localdir/dir/bob_data/file.model",
            FileStatus("file.model", 120, "FILE", 0, "read"),
            partial_mocked_store,
        )

    def test_target_doesnot_exists(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "storage", "file", True)
        op.copy_file = transfer_mock
        with pytest.raises(FileNotFoundError, match=r"Target should exist"):
            op.copy(
                urlparse("storage:///platform_existing/"),
                urlparse("file:///localdir_non_existing/dir/"),
                partial_mocked_store,
            )

        transfer_mock.assert_not_called()

    def test_source_doesnot_exists(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()
        op = CopyOperation.create("alice", "storage", "file", True)

        op.copy_file = transfer_mock
        with pytest.raises(FileNotFoundError, match=r"Source file not found."):
            op.copy(
                urlparse("storage:///platform_existing/abracadabra.txt"),
                urlparse("/localdir/dir/"),
                partial_mocked_store,
            )
        transfer_mock.assert_not_called()

    def test_target_is_file(self, mocked_store, partial_mocked_store, monkeypatch):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "storage", "file", True)
        op.copy_file = transfer_mock
        with pytest.raises(NotADirectoryError, match=r"Target should be directory"):
            op.copy(
                urlparse("storage:///platform_existing/"),
                urlparse("file:///localdir/abc.txt/"),
                partial_mocked_store,
            )

        transfer_mock.assert_not_called()


class TestCopyNonRecursivePlatformToLocal:
    def _structure(self, mocked_store, monkeypatch):
        monkeypatch.setattr(os.path, "exists", _os_exists(local_tree))
        monkeypatch.setattr(os.path, "isdir", _os_isdir(local_tree))
        monkeypatch.setattr(os, "mkdir", Mock())
        mocked_store.ls = _platform_ls(platform_tree)
        mocked_store.stats = _platform_stat(platform_tree)

    def test_source_dir(self, mocked_store, partial_mocked_store, monkeypatch):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "storage", "file", False)
        op.copy_file = transfer_mock
        with pytest.raises(
            ResourceNotFound, match=r"Source file /platform_existing/ not found"
        ):
            op.copy(
                urlparse("storage:///platform_existing/"),
                urlparse("file:///localdir/dir/"),
                partial_mocked_store,
            )

        transfer_mock.assert_not_called()

    def test_source_file(self, mocked_store, partial_mocked_store, monkeypatch):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "storage", "file", False)
        op.copy_file = transfer_mock
        op.copy(
            urlparse("storage:///platform_existing/my_file.txt"),
            urlparse("file:///localdir/dir/"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/alice/platform_existing/my_file.txt",
            "/localdir/dir/my_file.txt",
            FileStatus("my_file.txt", 100, "FILE", 0, "read"),
            partial_mocked_store,
        )

    def test_source_file_target_specified(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "storage", "file", False)
        op.copy_file = transfer_mock
        op.copy(
            urlparse("storage:///platform_existing/my_file.txt"),
            urlparse("file:///localdir/dir/dummy.txt"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/alice/platform_existing/my_file.txt",
            "/localdir/dir/dummy.txt",
            FileStatus("my_file.txt", 100, "FILE", 0, "read"),
            partial_mocked_store,
        )

    def test_target_doesnot_exists(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "storage", "file", False)
        op.copy_file = transfer_mock
        with pytest.raises(NotADirectoryError, match=r"Target should exist"):
            op.copy(
                urlparse("storage:///platform_existing/my_file.txt"),
                urlparse("file:///localdir_non_existing/dir/"),
                partial_mocked_store,
            )

        transfer_mock.assert_not_called()
