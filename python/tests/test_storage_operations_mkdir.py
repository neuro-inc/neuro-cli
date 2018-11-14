from unittest.mock import patch

import aiohttp
import pytest

from neuromation.cli.command_handlers import PlatformMakeDirOperation
from tests.utils import JsonResponse, mocked_async_context_manager


@pytest.fixture()
def alice_mkdir():
    return PlatformMakeDirOperation("alice")


@pytest.mark.asyncio
class TestNormalCases:
    async def test_fix_leading_platform_slash(self, alice_mkdir, partial_mocked_store):
        partial_mocked_store().patch("mkdirs", None)
        await alice_mkdir.mkdir("storage:data", partial_mocked_store)
        partial_mocked_store().mkdirs.assert_called_once()
        partial_mocked_store().mkdirs.assert_called_with(path="/alice/data")

    async def test_self_principal(self, alice_mkdir, partial_mocked_store):
        partial_mocked_store().patch("mkdirs", None)
        await alice_mkdir.mkdir("storage://~/data", partial_mocked_store)
        partial_mocked_store().mkdirs.assert_called_once()
        partial_mocked_store().mkdirs.assert_called_with(path="/alice/data")

    async def test_no_principal(self, alice_mkdir, partial_mocked_store):
        partial_mocked_store().patch("mkdirs", None)
        await alice_mkdir.mkdir("storage:/data", partial_mocked_store)
        partial_mocked_store().mkdirs.assert_called_once()
        partial_mocked_store().mkdirs.assert_called_with(path="/alice/data")

    async def test_with_principal(self, alice_mkdir, partial_mocked_store):
        partial_mocked_store().patch("mkdirs", None)
        await alice_mkdir.mkdir("storage://alice/data", partial_mocked_store)
        partial_mocked_store().mkdirs.assert_called_once()
        partial_mocked_store().mkdirs.assert_called_with(path="/alice/data")

    async def test_with_principal_file(self, alice_mkdir, partial_mocked_store):
        partial_mocked_store().patch("mkdirs", None)
        await alice_mkdir.mkdir("storage://alice/data/foo.txt", partial_mocked_store)
        partial_mocked_store().mkdirs.assert_called_once()
        partial_mocked_store().mkdirs.assert_called_with(path="/alice/data/foo.txt")

    async def test_with_principal_bob_file(self, alice_mkdir, partial_mocked_store):
        partial_mocked_store().patch("mkdirs", None)
        await alice_mkdir.mkdir("storage://bob/data/foo.txt", partial_mocked_store)
        partial_mocked_store().mkdirs.assert_called_once()
        partial_mocked_store().mkdirs.assert_called_with(path="/bob/data/foo.txt")

    async def test_with_principal_file_ensure_slash(
        self, alice_mkdir, partial_mocked_store
    ):
        partial_mocked_store().patch("mkdirs", None)
        await alice_mkdir.mkdir("storage://alice/data/foo.txt/", partial_mocked_store)
        partial_mocked_store().mkdirs.assert_called_once()
        partial_mocked_store().mkdirs.assert_called_with(path="/alice/data/foo.txt")

    async def test_list_root(self, alice_mkdir, partial_mocked_store):
        partial_mocked_store().patch("mkdirs", None)
        await alice_mkdir.mkdir("storage:", partial_mocked_store)
        partial_mocked_store().mkdirs.assert_called_once()
        partial_mocked_store().mkdirs.assert_called_with(path="/alice")

    async def test_list_root_2(self, alice_mkdir, partial_mocked_store):
        partial_mocked_store().patch("mkdirs", None)
        await alice_mkdir.mkdir("storage:/", partial_mocked_store)
        partial_mocked_store().mkdirs.assert_called_once()
        partial_mocked_store().mkdirs.assert_called_with(path="/alice")


@pytest.mark.asyncio
class TestInvalidScenarios:
    async def test_local(self, alice_mkdir, partial_mocked_store):
        with pytest.raises(
            ValueError, match=r"Path should be targeting platform storage."
        ):
            await alice_mkdir.mkdir("/home/dir", partial_mocked_store)

    async def test_http(self, alice_mkdir, partial_mocked_store):
        with pytest.raises(
            ValueError, match=r"Path should be targeting platform storage."
        ):
            await alice_mkdir.mkdir("http:///home/dir", partial_mocked_store)


@pytest.mark.asyncio
async def test_mkdir_alice_no_user(alice_mkdir, http_backed_storage):
    with patch("neuromation.cli.rc.Config.get_platform_user_name", new="alice"):
        with patch(
            "aiohttp.ClientSession.request",
            new=mocked_async_context_manager(JsonResponse({})),
        ):
            await alice_mkdir.mkdir("storage:///foo", http_backed_storage)
            aiohttp.ClientSession.request.assert_called_with(
                method="PUT",
                json=None,
                url="http://127.0.0.1/storage/alice/foo",
                params="MKDIRS",
                data=None,
            )
