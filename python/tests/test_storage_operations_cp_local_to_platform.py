import asyncio
import os
from typing import Callable, Dict, List
from unittest.mock import Mock
from urllib.parse import urlparse

import pytest

from neuromation.cli.command_handlers import CopyOperation, NonRecursiveLocalToPlatform
from neuromation.client import FileStatus, IllegalArgumentError, ResourceNotFound


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
    async def ls(path: str):
        coll = [v for v in dirs if v["path"] == path]
        if len(coll) == 0:
            raise IllegalArgumentError("Not a directory.")
        if "file" not in coll[0]:
            return coll[0]["files"]
        raise IllegalArgumentError("Not a directory.")

    return ls


def _platform_stat(dirs: List) -> Callable:
    async def stat(path: str):
        try:
            item = next(v for v in dirs if v["path"] == path)
            if item:
                if item.get("file", False):
                    return item.get("files")[0]
                else:
                    return FileStatus(
                        path=path,
                        size=0,
                        type="DIRECTORY",
                        modification_time=0,
                        permission="",
                    )
            raise IllegalArgumentError("Not a directory.")
        except StopIteration:
            raise ResourceNotFound()

    return stat


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
    {
        "path": "/alice/platform_existing/my_file.txt",
        "files": [FileStatus("my_file.txt", 100, "FILE", 0, "read")],
        "file": True,
    },
    {"path": "/bob", "files": [FileStatus("bob_data", 0, "DIRECTORY", 0, "read")]},
    {
        "path": "/bob/bob_data",
        "files": [FileStatus("file.model", 120, "FILE", 0, "read")],
    },
    {
        "path": "/bob/bob_data/file.model",
        "files": [FileStatus("file.model", 120, "FILE", 0, "read")],
        "file": True,
    },
]


@pytest.mark.asyncio
class TestCopyRecursiveLocalToPlatform:
    def _structure(self, mocked_store, monkeypatch):
        monkeypatch.setattr(os.path, "exists", _os_exists(local_tree))
        monkeypatch.setattr(os.path, "isdir", _os_isdir(local_tree))
        monkeypatch.setattr(os, "walk", _os_walk_func(local_tree))
        monkeypatch.setattr(os, "mkdir", Mock())
        mocked_store.ls = _platform_ls(platform_tree)
        mocked_store.stats = _platform_stat(platform_tree)

    def _side_mock(self) -> Mock:
        f = asyncio.Future()
        f.set_result(None)

        my_mock = Mock()
        my_mock.return_value = f
        return my_mock

    async def test_source_file(self, mocked_store, partial_mocked_store, monkeypatch):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = self._side_mock()

        op = CopyOperation.create("alice", "file", "storage", True)
        NonRecursiveLocalToPlatform.copy_file = transfer_mock
        await op.copy(
            urlparse("file:///localdir/abc.txt/"),
            urlparse("storage:///platform_existing/my_file.txt"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1

    async def test_ok(self, mocked_store, partial_mocked_store, monkeypatch):
        partial_mocked_store().patch("mkdirs", None)
        self._structure(mocked_store, monkeypatch)
        mock = self._side_mock()

        op = CopyOperation.create("alice", "file", "storage", True)
        op.copy_file = mock
        await op.copy(
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

    async def test_ok_copy_bob_data(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        partial_mocked_store().patch("mkdirs", None)
        self._structure(mocked_store, monkeypatch)
        transfer_mock = self._side_mock()

        op = CopyOperation.create("alice", "file", "storage", True)
        op.copy_file = transfer_mock
        await op.copy(
            urlparse("file:///localdir/"),
            urlparse("storage://bob/"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/localdir/abc.txt", "/bob/localdir/abc.txt", partial_mocked_store
        )

    async def test_ok_copy_into_root_data(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        partial_mocked_store().patch("mkdirs", None)
        self._structure(mocked_store, monkeypatch)
        transfer_mock = self._side_mock()

        op = CopyOperation.create("alice", "file", "storage", True)
        op.copy_file = transfer_mock
        await op.copy(
            urlparse("file:///localdir/"), urlparse("storage:///"), partial_mocked_store
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/localdir/abc.txt", "/alice/localdir/abc.txt", partial_mocked_store
        )

    async def test_source_doesnot_exists(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = self._side_mock()

        op = CopyOperation.create("alice", "file", "storage", True)
        op.copy_file = transfer_mock
        with pytest.raises(ValueError, match=r"Source should exist"):
            await op.copy(
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


@pytest.mark.asyncio
class TestCopyNonRecursivePlatformToLocal:
    def _structure(self, mocked_store, monkeypatch):
        monkeypatch.setattr(os.path, "exists", _os_exists(local_tree))
        monkeypatch.setattr(os.path, "isdir", _os_isdir(local_tree))
        monkeypatch.setattr(os, "walk", _os_walk_func(local_tree))
        monkeypatch.setattr(os, "mkdir", Mock())
        mocked_store.patch_func(mocked_store.ls, _platform_ls(platform_tree))
        mocked_store.patch_func(mocked_store.stats, _platform_stat(platform_tree))

    def _side_mock(self) -> Mock:
        f = asyncio.Future()
        f.set_result(None)

        my_mock = Mock()
        my_mock.return_value = f
        return my_mock

    async def test_source_not_found(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = self._side_mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        with pytest.raises(FileNotFoundError, match=r"Source file not found"):
            await op.copy(
                urlparse("file:///local_non_existing/file.txt"),
                urlparse("storage:///platform_existing/"),
                partial_mocked_store,
            )

        transfer_mock.assert_not_called()

    async def test_source_is_dir(self, mocked_store, partial_mocked_store, monkeypatch):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = self._side_mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        with pytest.raises(IsADirectoryError, match=r"Source should be file."):
            await op.copy(
                urlparse("file:///localdir/"),
                urlparse("storage:///platform_existing/"),
                partial_mocked_store,
            )

        transfer_mock.assert_not_called()

    async def test_source_file_target_dir(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = self._side_mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        await op.copy(
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

    async def test_source_file_target_root_trailing_slash(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = self._side_mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        await op.copy(
            urlparse("file:///localdir/abc.txt"),
            urlparse("storage:///"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/localdir/abc.txt", "/alice/abc.txt", partial_mocked_store
        )

    async def test_source_file_target_root_no_trailing_slash(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = self._side_mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        await op.copy(
            urlparse("file:///localdir/abc.txt"),
            urlparse("storage://"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/localdir/abc.txt", "/alice/abc.txt", partial_mocked_store
        )

    async def test_source_file_target_empty(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = self._side_mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        await op.copy(
            urlparse("file:///localdir/abc.txt"),
            urlparse("storage:"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/localdir/abc.txt", "/alice/abc.txt", partial_mocked_store
        )

    async def test_source_file_target_does_not_exists(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = self._side_mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        non_exist = "storage:///not-exists/not-exists/not-exists"
        with pytest.raises(
            NotADirectoryError, match=r"Target directory does not exist."
        ):
            await op.copy(
                urlparse("file:///localdir/abc.txt"),
                urlparse("%s" % non_exist),
                partial_mocked_store,
            )

        assert transfer_mock.call_count == 0

    async def test_source_file_target_slash(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = self._side_mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        await op.copy(
            urlparse("file:///localdir/abc.txt"),
            urlparse("storage:/"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/localdir/abc.txt", "/alice/abc.txt", partial_mocked_store
        )

    async def test_target_file(self, mocked_store, partial_mocked_store, monkeypatch):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = self._side_mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        await op.copy(
            urlparse("file:///localdir/abc.txt"),
            urlparse("storage:///platform_existing/dir2"),
            partial_mocked_store,
        )

        assert transfer_mock.call_count == 1
        transfer_mock.assert_any_call(
            "/localdir/abc.txt", "/alice/platform_existing/dir2", partial_mocked_store
        )

    async def test_target_file_trailing_slash(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        with pytest.raises(
            NotADirectoryError, match=r"Target directory does not exist."
        ):
            await op.copy(
                urlparse("file:///localdir/abc.txt"),
                urlparse("storage:///platform_existing/dir2/"),
                partial_mocked_store,
            )

    async def test_target_file_trailing_slash_2(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = Mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        with pytest.raises(
            NotADirectoryError, match=r"Target directory does not exist."
        ):
            await op.copy(
                urlparse("file:///localdir/abc.txt"),
                urlparse("storage:///platform_existing/my_file.txt/"),
                partial_mocked_store,
            )

    async def test_target_dir(self, mocked_store, partial_mocked_store, monkeypatch):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = self._side_mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        await op.copy(
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

    async def test_target_dir_trailing_slash(
        self, mocked_store, partial_mocked_store, monkeypatch
    ):
        self._structure(mocked_store, monkeypatch)
        transfer_mock = self._side_mock()

        op = CopyOperation.create("alice", "file", "storage", False)
        op.copy_file = transfer_mock
        await op.copy(
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
