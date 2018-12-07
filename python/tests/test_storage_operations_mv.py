from unittest.mock import patch

import aiohttp
import pytest

from neuromation.cli.command_handlers import PlatformRenameOperation
from tests.utils import JsonResponse, mocked_async_context_manager


@pytest.fixture
def alice_op():
    return PlatformRenameOperation("alice")


class TestNormalCases:
    # this test suite follows ones for ls operation

    def test_mv_existing_file_to_phantom_file(self, alice_op, partial_mocked_store):
        pms = partial_mocked_store
        alice_op.mv("storage://", "storage:", pms)
        pms().mv.assert_called_once()
        pms().mv.assert_called_with(src_path="/", dst_path="/alice")

    def test_fix_leading_platform_slash(self, alice_op, partial_mocked_store):
        pms = partial_mocked_store
        alice_op.mv("storage://data", "storage://data2", pms)
        pms().mv.assert_called_once()
        pms().mv.assert_called_with(src_path="/data", dst_path="/data2")

    def test_self_principal(self, alice_op, partial_mocked_store):
        pms = partial_mocked_store
        alice_op.mv("storage://~/data", "storage://~/data2", pms)
        pms().mv.assert_called_once()
        pms().mv.assert_called_with(src_path="/alice/data", dst_path="/alice/data2")

    def test_no_principal(self, alice_op, partial_mocked_store):
        pms = partial_mocked_store
        alice_op.mv("storage:/data", "storage:/data2", pms)
        pms().mv.assert_called_once()
        pms().mv.assert_called_with(src_path="/alice/data", dst_path="/alice/data2")

    def test_with_principal(self, alice_op, partial_mocked_store):
        pms = partial_mocked_store
        alice_op.mv("storage://alice/data", "storage://alice/data2", pms)
        pms().mv.assert_called_once()
        pms().mv.assert_called_with(src_path="/alice/data", dst_path="/alice/data2")

    def test_with_principal_file(self, alice_op, partial_mocked_store):
        pms = partial_mocked_store
        alice_op.mv("storage://alice/data/foo.txt", "storage:/data/bar.txt", pms)
        pms().mv.assert_called_once()
        pms().mv.assert_called_with(
            src_path="/alice/data/foo.txt", dst_path="/alice/data/bar.txt"
        )

    def test_with_principal_bob_file(self, alice_op, partial_mocked_store):
        pms = partial_mocked_store
        alice_op.mv("storage://bob/data/foo.txt", "storage://bob/data/bar.txt", pms)
        pms().mv.assert_called_once()
        pms().mv.assert_called_with(
            src_path="/bob/data/foo.txt", dst_path="/bob/data/bar.txt"
        )

    def test_with_principal_file_ensure_slash(self, alice_op, partial_mocked_store):
        pms = partial_mocked_store
        alice_op.mv(
            "storage://alice/data/foo.txt/", "storage://alice/data/bar.txt/", pms
        )
        pms().mv.assert_called_once()
        pms().mv.assert_called_with(
            src_path="/alice/data/foo.txt", dst_path="/alice/data/bar.txt"
        )

    def test_mv_to_root(self, alice_op, partial_mocked_store):
        pms = partial_mocked_store
        alice_op.mv("storage:", "storage:/", pms)
        pms().mv.assert_called_once()
        pms().mv.assert_called_with(src_path="/alice", dst_path="/alice")


class TestInvalidScenarios:
    def test_mv_from_local(self, alice_op, partial_mocked_store):
        pms = partial_mocked_store
        with pytest.raises(
            ValueError, match=r"Path should be targeting platform storage."
        ):
            alice_op.mv("/home/dir", "storage:///home/dir2", pms)

    def test_mv_to_local(self, alice_op, partial_mocked_store):
        pms = partial_mocked_store
        with pytest.raises(
            ValueError, match=r"Path should be targeting platform storage."
        ):
            alice_op.mv("storage:///home/dir", "/home/dir2", pms)

    def test_mv_from_http(self, alice_op, partial_mocked_store):
        pms = partial_mocked_store
        with pytest.raises(
            ValueError, match=r"Path should be targeting platform storage."
        ):
            alice_op.mv("http:///home/dir", "storage:///home/dir2", pms)

    def test_mv_to_http(self, alice_op, partial_mocked_store):
        pms = partial_mocked_store
        with pytest.raises(
            ValueError, match=r"Path should be targeting platform storage."
        ):
            alice_op.mv("storage:///home/dir", "http:///home/di2", pms)


empty_response = JsonResponse({})


@patch(
    "aiohttp.ClientSession.request", new=mocked_async_context_manager(empty_response)
)
@patch("neuromation.cli.rc.Config.get_platform_user_name", new="alice")
def test_mv_alice_no_user(alice_op, http_backed_storage):
    alice_op.mv("storage:///foo", "storage:///bar", http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method="POST",
        json=None,
        url="http://127.0.0.1/storage/alice/foo",
        params={"op": "RENAME", "destination": "/alice/bar"},
        headers=None,
        data=None,
    )


@patch(
    "aiohttp.ClientSession.request", new=mocked_async_context_manager(empty_response)
)
@patch("neuromation.cli.rc.Config.get_platform_user_name", new="alice")
def test_mv_alice_tilde_user(alice_op, http_backed_storage):
    alice_op.mv("storage://~/foo", "storage:///bar", http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method="POST",
        json=None,
        url="http://127.0.0.1/storage/alice/foo",
        params={"op": "RENAME", "destination": "/alice/bar"},
        headers=None,
        data=None,
    )


@patch(
    "aiohttp.ClientSession.request", new=mocked_async_context_manager(empty_response)
)
@patch("neuromation.cli.rc.Config.get_platform_user_name", new="alice")
def test_mv_alice_omitted_user(alice_op, http_backed_storage):
    alice_op.mv("storage:/foo", "storage:///bar", http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method="POST",
        json=None,
        url="http://127.0.0.1/storage/alice/foo",
        params={"op": "RENAME", "destination": "/alice/bar"},
        headers=None,
        data=None,
    )


@patch(
    "aiohttp.ClientSession.request", new=mocked_async_context_manager(empty_response)
)
@patch("neuromation.cli.rc.Config.get_platform_user_name", new="alice")
def test_mv_alice_omitted_user_no_leading_slash(alice_op, http_backed_storage):
    alice_op.mv("storage:foo", "storage:///bar", http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method="POST",
        json=None,
        url="http://127.0.0.1/storage/alice/foo",
        params={"op": "RENAME", "destination": "/alice/bar"},
        headers=None,
        data=None,
    )


@patch(
    "aiohttp.ClientSession.request", new=mocked_async_context_manager(empty_response)
)
@patch("neuromation.cli.rc.Config.get_platform_user_name", new="alice")
def test_mv_alice_removes_bob_data(alice_op, http_backed_storage):
    alice_op.mv("storage://bob/foo", "storage:///bar", http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method="POST",
        json=None,
        url="http://127.0.0.1/storage/bob/foo",
        params={"op": "RENAME", "destination": "/alice/bar"},
        headers=None,
        data=None,
    )


@patch(
    "aiohttp.ClientSession.request", new=mocked_async_context_manager(empty_response)
)
@patch("neuromation.cli.rc.Config.get_platform_user_name", new="alice")
def test_mv_alice_removes_bob_data_file(alice_op, http_backed_storage):
    alice_op.mv("storage://bob/foo/data.txt/", "storage:///bar", http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method="POST",
        json=None,
        url="http://127.0.0.1/storage/bob/foo/data.txt",
        params={"op": "RENAME", "destination": "/alice/bar"},
        headers=None,
        data=None,
    )
