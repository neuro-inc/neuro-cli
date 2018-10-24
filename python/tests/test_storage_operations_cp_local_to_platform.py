import os
from typing import Callable, Dict, List
from unittest.mock import Mock
from urllib.parse import urlparse

import pytest

from neuromation.cli.command_handlers import CopyOperation, \
    NonRecursiveLocalToPlatform
from neuromation.client import FileStatus, IllegalArgumentError


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


def _os_walk_func(tree: Dict) -> Callable:
    def scan(root: Dict, path: str) -> List:
        result = []
        presult = []

        files = []
        subdirs = []
        for node in root["c"]:
            if root["c"][node]["_dir"]:
                subdirs.append(node)
                src_path = path + "/" + node if path != "/" else "/" + node
                presult.extend(scan(root["c"][node], src_path))
            else:
                files.append(node)
        result.append((path, subdirs, files))
        result.extend(presult)
        return result

    def check(src: str):
        root = tree
        parts = src.split("/")
        for part in parts:
            if not part:
                continue
            if part in root["c"]:
                root = root["c"][part]
            else:
                return []

        return scan(root, src)

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
        coll = [v for v in dirs if v["path"] == path]
        if len(coll) == 0:
            raise IllegalArgumentError("Not a directory.")
        if "file" not in coll[0]:
            return coll[0]["files"]
        raise IllegalArgumentError("Not a directory.")

    return ls


local_tree = {
    "c": {
        "localdir": {
            "c": {"dir": {"c": {}, "_dir": True}, "abc.txt": {"_dir": False}},
            "_dir": True,
        },
        "dry.exe": {"c": {}, "_dir": False},
    },
    "_dir": True,
}

platform_tree = [
    {
        "path": "/",
        "files": [
            FileStatus("/alice", 0, "DIRECTORY"),
            FileStatus("/bob", 0, "DIRECTORY"),
        ],
    },
    {"path": "/alice", "files": [FileStatus("platform_existing", 0, "DIRECTORY")]},
    {
        "path": "/alice/platform_existing",
        "files": [
            FileStatus("my_file.txt", 100, "FILE"),
            FileStatus("dir", 0, "DIRECTORY"),
            FileStatus("di1", 0, "DIRECTORY"),
        ],
    },
    {
        "path": "/alice/platform_existing/dir",
        "files": [FileStatus("my_file2.txt", 100, "FILE")],
    },
    {"path": "/alice/platform_existing/di1", "files": []},
    {
        "path": "/alice/platform_existing/my_file.txt",
        "files": [FileStatus("my_file.txt", 100, "FILE")],
        "file": True,
    },
    {"path": "/bob", "files": [FileStatus("bob_data", 0, "DIRECTORY")]},
    {"path": "/bob/bob_data", "files": [FileStatus("file.model", 120, "FILE")]},
    {
        "path": "/bob/bob_data/file.model",
        "files": [FileStatus("file.model", 120, "FILE")],
        "file": True,
    },
]


class TestCopyRecursiveLocalToPlatform:
    def _structure(self, mocked_store, monkeypatch):
        monkeypatch.setattr(os.path, "exists", _os_exists(local_tree))
        monkeypatch.setattr(os.path, "isdir", _os_isdir(local_tree))
        monkeypatch.setattr(os, "walk", _os_walk_func(local_tree))
        monkeypatch.setattr(os, "mkdir", Mock())
        mocked_store.ls = _platform_ls(platform_tree)

    def test_source_file(self, mocked_store, partial_mocked_store, monkeypatch):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", True)
        NonRecursiveLocalToPlatform.copy_file = transfer_mock
        op.copy(
            urlparse("file:///localdir/abc.txt/"),
            urlparse("storage:///platform_existing/my_file.txt"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1

    def test_ok(self, mocked_store, partial_mocked_store, monkeypatch):
        self._structure(mocked_store, monkeypatch)
        mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", True)
        op.copy_file = mock
        op.copy(
            urlparse("file:///"),
            urlparse("storage:///platform_existing/"),
            partial_mocked_store,
        )

        assert mock.call_count == 2
        mock.assert_any_call(
            "/dry.exe", "/alice/platform_existing/dry.exe", partial_mocked_store
        )
        mock.assert_any_call(
            "/localdir/abc.txt",
            "/alice/platform_existing/localdir/abc.txt",
            partial_mocked_store,
        )

    def test_ok_copy_bob_data(self, mocked_store, partial_mocked_store, monkeypatch):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", True)
        op.copy_file = transfer_mock
        op.copy(
            urlparse("file:///localdir/"),
            urlparse("storage://bob/"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/localdir/abc.txt", "/bob/localdir/abc.txt", partial_mocked_store
        )

    def test_ok_copy_into_root_data(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", True)
        op.copy_file = transfer_mock
        op.copy(
            urlparse("file:///localdir/"), urlparse("storage:///"), partial_mocked_store
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/localdir/abc.txt", "/alice/localdir/abc.txt", partial_mocked_store
        )

    def test_source_doesnot_exists(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", True)
        op.copy_file = transfer_mock
        with pytest.raises(ValueError, match=r"Source should exist"):
            op.copy(
                urlparse("file:///non_existing/"),
                urlparse("storage:///"),
                partial_mocked_store,
            )

        transfer_mock.assert_not_called()

    # TODO
    # def test_target_doesnot_exists(self,
    #                                mocked_store, partial_mocked_store,
    #                                monkeypatch):
    #     self._structure(mocked_store, monkeypatch)
    #     transfer_mock = Mock()
    #
    #     op = CopyOperation.create('alice', 'file', 'storage', True)
    #     op.copy_file = transfer_mock
    #     with pytest.raises(ValueError, match=r'Target should exist'):
    #         op.copy(urlparse('file:///localdir/'),
    #                 urlparse('storage:///platform_non_existing/'),
    #                 partial_mocked_store)
    #
    #     transfer_mock.assert_not_called()

    # TODO
    # def test_target_is_file(self,
    #                         mocked_store, partial_mocked_store, monkeypatch):
    #     self._structure(mocked_store, monkeypatch)
    #     transfer_mock = Mock()
    #
    #     op = CopyOperation.create('alice', 'file', 'storage', True)
    #     op.copy_file = transfer_mock
    #     with pytest.raises(ValueError, match=r'Target should be directory'):
    #         op.copy(urlparse('file:///localdir/abc.txt/'),
    #                 urlparse('storage:///platform_existing/abc.txt'),
    #                 partial_mocked_store)
    #
    #     transfer_mock.assert_not_called()


class TestCopyNonRecursivePlatformToLocal:
    def _structure(self, mocked_store, monkeypatch):
        monkeypatch.setattr(os.path, "exists", _os_exists(local_tree))
        monkeypatch.setattr(os.path, "isdir", _os_isdir(local_tree))
        monkeypatch.setattr(os, "walk", _os_walk_func(local_tree))
        monkeypatch.setattr(os, "mkdir", Mock())
        mocked_store.ls = _platform_ls(platform_tree)

    def test_source_not_found(self, mocked_store, partial_mocked_store, monkeypatch):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        with pytest.raises(FileNotFoundError, match=r"Source file not found"):
            op.copy(
                urlparse("file:///local_non_existing/file.txt"),
                urlparse("storage:///platform_existing/"),
                partial_mocked_store,
            )

        transfer_mock.assert_not_called()

    def test_source_is_dir(self, mocked_store, partial_mocked_store, monkeypatch):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        with pytest.raises(IsADirectoryError, match=r"Source should be file."):
            op.copy(
                urlparse("file:///localdir/"),
                urlparse("storage:///platform_existing/"),
                partial_mocked_store,
            )

        transfer_mock.assert_not_called()

    def test_source_file_target_dir(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        op.copy(
            urlparse("file:///localdir/abc.txt"),
            urlparse("storage:///platform_existing/"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/localdir/abc.txt",
            "/alice/platform_existing/abc.txt",
            partial_mocked_store,
        )

    def test_source_file_target_root_trailing_slash(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        op.copy(
            urlparse("file:///localdir/abc.txt"),
            urlparse("storage:///"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/localdir/abc.txt", "/alice/abc.txt", partial_mocked_store
        )

    def test_source_file_target_root_no_trailing_slash(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        op.copy(
            urlparse("file:///localdir/abc.txt"),
            urlparse("storage://"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/localdir/abc.txt", "/alice/abc.txt", partial_mocked_store
        )

    def test_source_file_target_empty(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        op.copy(
            urlparse("file:///localdir/abc.txt"),
            urlparse("storage:"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/localdir/abc.txt", "/alice/abc.txt", partial_mocked_store
        )

    def test_source_file_target_does_not_exists(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        non_exist = "storage:///not-exists/not-exists/not-exists"
        with pytest.raises(
            NotADirectoryError, match=r"Target directory does not exist."
        ):
            op.copy(
                urlparse("file:///localdir/abc.txt"),
                urlparse("%s" % non_exist),
                partial_mocked_store,
            )

        assert transfer_mock.call_count == 0

    def test_source_file_target_slash(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        op.copy(
            urlparse("file:///localdir/abc.txt"),
            urlparse("storage:/"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/localdir/abc.txt", "/alice/abc.txt", partial_mocked_store
        )

    def test_target_file(self, mocked_store, partial_mocked_store, monkeypatch):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        op.copy(
            urlparse("file:///localdir/abc.txt"),
            urlparse("storage:///platform_existing/dir2"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/localdir/abc.txt", "/alice/platform_existing/dir2", partial_mocked_store
        )

    def test_target_file_trailing_slash(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        with pytest.raises(
            NotADirectoryError, match=r"Target directory does not exist."
        ):
            op.copy(
                urlparse("file:///localdir/abc.txt"),
                urlparse("storage:///platform_existing/dir2/"),
                partial_mocked_store,
            )

    def test_target_file_trailing_slash_2(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        with pytest.raises(
            NotADirectoryError, match=r"Target directory does not exist."
        ):
            op.copy(
                urlparse("file:///localdir/abc.txt"),
                urlparse("storage:///platform_existing/my_file.txt/"),
                partial_mocked_store,
            )

    def test_target_dir(self, mocked_store, partial_mocked_store, monkeypatch):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        op.copy(
            urlparse("file:///localdir/abc.txt"),
            urlparse("storage:///platform_existing/di1"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/localdir/abc.txt",
            "/alice/platform_existing/di1/abc.txt",
            partial_mocked_store,
        )

    def test_target_dir_trailing_slash(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        op.copy(
            urlparse("file:///localdir/abc.txt"),
            urlparse("storage:///platform_existing/di1/"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/localdir/abc.txt",
            "/alice/platform_existing/di1/abc.txt",
            partial_mocked_store,
        )
