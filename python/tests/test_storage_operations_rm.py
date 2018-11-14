from unittest import mock

import pytest

from neuromation.cli.command_handlers import PlatformRemoveOperation
from tests.utils import PlainResponse, mocked_async_context_manager


@pytest.fixture()
def alice_rm():
    return PlatformRemoveOperation("alice")


@pytest.mark.asyncio
class TestNormalCases:
    async def test_fix_leading_platform_slash(self, alice_rm, partial_mocked_store):
        partial_mocked_store().patch("rm", None)
        await alice_rm.remove("storage:data", partial_mocked_store)
        partial_mocked_store().rm.assert_called_once()
        partial_mocked_store().rm.assert_called_with(path="/alice/data")

    async def test_self_principal(self, alice_rm, partial_mocked_store):
        partial_mocked_store().patch("rm", None)
        await alice_rm.remove("storage://~/data", partial_mocked_store)
        partial_mocked_store().rm.assert_called_once()
        partial_mocked_store().rm.assert_called_with(path="/alice/data")

    async def test_no_principal(self, alice_rm, partial_mocked_store):
        partial_mocked_store().patch("rm", None)
        await alice_rm.remove("storage:/data", partial_mocked_store)
        partial_mocked_store().rm.assert_called_once()
        partial_mocked_store().rm.assert_called_with(path="/alice/data")

    async def test_with_principal(self, alice_rm, partial_mocked_store):
        partial_mocked_store().patch("rm", None)
        await alice_rm.remove("storage://alice/data", partial_mocked_store)
        partial_mocked_store().rm.assert_called_once()
        partial_mocked_store().rm.assert_called_with(path="/alice/data")

    async def test_with_principal_file(self, alice_rm, partial_mocked_store):
        partial_mocked_store().patch("rm", None)
        await alice_rm.remove("storage://alice/data/foo.txt", partial_mocked_store)
        partial_mocked_store().rm.assert_called_once()
        partial_mocked_store().rm.assert_called_with(path="/alice/data/foo.txt")

    async def test_with_principal_bob_file(self, alice_rm, partial_mocked_store):
        partial_mocked_store().patch("rm", None)
        await alice_rm.remove("storage://bob/data/foo.txt", partial_mocked_store)
        partial_mocked_store().rm.assert_called_once()
        partial_mocked_store().rm.assert_called_with(path="/bob/data/foo.txt")

    async def test_with_principal_file_ensure_slash(
        self, alice_rm, partial_mocked_store
    ):
        partial_mocked_store().patch("rm", None)
        await alice_rm.remove("storage://alice/data/foo.txt/", partial_mocked_store)
        partial_mocked_store().rm.assert_called_once()
        partial_mocked_store().rm.assert_called_with(path="/alice/data/foo.txt")


@pytest.mark.asyncio
class TestInvalidScenarios:
    async def test_malformed_delete_home(self, alice_rm, partial_mocked_store):
        with pytest.raises(ValueError, match=r"Invalid path value."):
            await alice_rm.remove("storage:", partial_mocked_store)

    async def test_malformed_delete_other_home(self, alice_rm, partial_mocked_store):
        with pytest.raises(ValueError, match=r"Invalid path value."):
            await alice_rm.remove("storage://home/", partial_mocked_store)

    async def test_malformed_all_users(self, alice_rm, partial_mocked_store):
        with pytest.raises(ValueError, match=r"Invalid path value."):
            await alice_rm.remove("storage://", partial_mocked_store)

    async def test_local(self, alice_rm, partial_mocked_store):
        with pytest.raises(
            ValueError, match=r"Path should be targeting platform storage."
        ):
            await alice_rm.remove("/home/dir", partial_mocked_store)

    async def test_http(self, alice_rm, partial_mocked_store):
        with pytest.raises(
            ValueError, match=r"Path should be targeting platform storage."
        ):
            await alice_rm.remove("http:///home/dir", partial_mocked_store)


@pytest.mark.asyncio
async def test_rm_alice_no_user(alice_rm, http_backed_storage):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(PlainResponse(text="")),
    ) as my_mock:
        with mock.patch(
            "neuromation.cli.rc.Config.get_platform_user_name", new="alice"
        ):
            await alice_rm.remove("storage:///foo", http_backed_storage)
            my_mock.assert_called_with(
                method="DELETE",
                json=None,
                url="http://127.0.0.1/storage/alice/foo",
                params=None,
                data=None,
            )
