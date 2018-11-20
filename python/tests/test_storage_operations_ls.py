from unittest import mock
from unittest.mock import patch

import pytest

from neuromation.cli.command_handlers import PlatformListDirOperation
from tests.utils import JsonResponse, mocked_async_context_manager


@pytest.fixture()
def alice_ls():
    return PlatformListDirOperation("alice")


@pytest.mark.asyncio
class TestNormalCases:
    async def test_list_users(self, alice_ls, partial_mocked_store):
        partial_mocked_store().patch("ls", None)
        await alice_ls.ls("storage://", partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path="/")

    # The test below are commented out due to complexity of the algorithm.
    # Do not be brave uncommenting would sumon MustaKrakish
    # Brave person would need to implement various cases to handle
    # dots, double dots, and ensure that it would still work
    # with all the tricky cases when directory name is '.' or '..'
    #
    # def test_back_reference(self, alice_ls, partial_mocked_store):
    #     alice_ls.ls('storage://~/my_data_depth0/my_data_depth1/../',
    #                 partial_mocked_store)
    #     partial_mocked_store().ls.assert_called_once()
    #     partial_mocked_store().ls.assert_called_with(
    #         path='/alice/my_data_depth0')
    #
    # def test_back_reference_parent_of_root(self,
    #                                        alice_ls,
    #                                        partial_mocked_store):
    #     alice_ls.ls('storage://~/my_data_depth0/my_data_depth1/'
    #                 '../../../../../../../../../',
    #                 partial_mocked_store)
    #     partial_mocked_store().ls.assert_called_once()
    #     partial_mocked_store().ls.assert_called_with(path='/')
    #
    # def test_back_reference_parent_of_root_2(self,
    #                                          alice_ls,
    #                                          partial_mocked_store):
    #     alice_ls.ls('storage:/'
    #                 '../../../../../../../../../',
    #                 partial_mocked_store)
    #     partial_mocked_store().ls.assert_called_once()
    #     partial_mocked_store().ls.assert_called_with(path='/')

    async def test_fix_leading_platform_slash(self, alice_ls, partial_mocked_store):
        partial_mocked_store().patch("ls", None)
        await alice_ls.ls("storage:data", partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path="/alice/data")

    async def test_self_principal(self, alice_ls, partial_mocked_store):
        partial_mocked_store().patch("ls", None)
        await alice_ls.ls("storage://~/data", partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path="/alice/data")

    async def test_no_principal(self, alice_ls, partial_mocked_store):
        partial_mocked_store().patch("ls", None)
        await alice_ls.ls("storage:/data", partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path="/alice/data")

    async def test_with_principal(self, alice_ls, partial_mocked_store):
        partial_mocked_store().patch("ls", None)
        await alice_ls.ls("storage://alice/data", partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path="/alice/data")

    async def test_with_principal_file(self, alice_ls, partial_mocked_store):
        partial_mocked_store().patch("ls", None)
        await alice_ls.ls("storage://alice/data/foo.txt", partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path="/alice/data/foo.txt")

    async def test_with_principal_bob_file(self, alice_ls, partial_mocked_store):
        partial_mocked_store().patch("ls", None)
        await alice_ls.ls("storage://bob/data/foo.txt", partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path="/bob/data/foo.txt")

    async def test_with_principal_file_ensure_slash(
        self, alice_ls, partial_mocked_store
    ):
        partial_mocked_store().patch("ls", None)
        await alice_ls.ls("storage://alice/data/foo.txt/", partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path="/alice/data/foo.txt")

    async def test_list_root(self, alice_ls, partial_mocked_store):
        partial_mocked_store().patch("ls", None)
        await alice_ls.ls("storage:", partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path="/alice")

    async def test_list_root_2(self, alice_ls, partial_mocked_store):
        partial_mocked_store().patch("ls", None)
        await alice_ls.ls("storage:/", partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path="/alice")


@pytest.mark.asyncio
class TestInvalidScenarios:
    async def test_local(self, alice_ls, partial_mocked_store):
        with pytest.raises(
            ValueError, match=r"Path should be " r"targeting platform storage."
        ):
            await alice_ls.ls("/home/dir", partial_mocked_store)

    async def test_http(self, alice_ls, partial_mocked_store):
        with pytest.raises(
            ValueError, match=r"Path should be " r"targeting platform storage."
        ):
            await alice_ls.ls("http:///home/dir", partial_mocked_store)


empty_response = JsonResponse({"FileStatuses": {"FileStatus": []}})


@pytest.mark.asyncio
class TestListHttpLayer:
    async def test_ls_alice_no_user(self, alice_ls, http_backed_storage):
        with mock.patch(
            "aiohttp.ClientSession.request",
            new=mocked_async_context_manager(empty_response),
        ) as my_mock:
            with mock.patch(
                "neuromation.cli.rc.Config.get_platform_user_name", new="alice"
            ):
                await alice_ls.ls("storage:///foo", http_backed_storage)
                my_mock.assert_called_with(
                    method="GET",
                    json=None,
                    url="http://127.0.0.1/storage/alice/foo",
                    params="LISTSTATUS",
                    data=None,
                )

    async def test_ls_alice_tilde_user(self, alice_ls, http_backed_storage):
        with mock.patch(
            "aiohttp.ClientSession.request",
            new=mocked_async_context_manager(empty_response),
        ) as my_mock:
            with patch("neuromation.cli.rc.Config.get_platform_user_name", new="alice"):
                await alice_ls.ls("storage://~/foo", http_backed_storage)
                my_mock.assert_called_with(
                    method="GET",
                    json=None,
                    url="http://127.0.0.1/storage/alice/foo",
                    params="LISTSTATUS",
                    data=None,
                )

    async def test_ls_alice_omitted_user(self, alice_ls, http_backed_storage):
        with mock.patch(
            "aiohttp.ClientSession.request",
            new=mocked_async_context_manager(empty_response),
        ) as my_mock:
            with mock.patch(
                "neuromation.cli.rc.Config.get_platform_user_name", new="alice"
            ):
                await alice_ls.ls("storage:/foo", http_backed_storage)
                my_mock.assert_called_with(
                    method="GET",
                    json=None,
                    url="http://127.0.0.1/storage/alice/foo",
                    params="LISTSTATUS",
                    data=None,
                )

    async def test_ls_alice_omitted_user_no_leading_slash(
        self, alice_ls, http_backed_storage
    ):
        with mock.patch(
            "aiohttp.ClientSession.request",
            new=mocked_async_context_manager(empty_response),
        ) as my_mock:
            with patch("neuromation.cli.rc.Config.get_platform_user_name", new="alice"):
                await alice_ls.ls("storage:foo", http_backed_storage)
                my_mock.assert_called_with(
                    method="GET",
                    json=None,
                    url="http://127.0.0.1/storage/alice/foo",
                    params="LISTSTATUS",
                    data=None,
                )

    async def test_ls_alice_removes_bob_data(self, alice_ls, http_backed_storage):
        with mock.patch(
            "aiohttp.ClientSession.request",
            new=mocked_async_context_manager(empty_response),
        ) as my_mock:
            with patch("neuromation.cli.rc.Config.get_platform_user_name", new="alice"):
                await alice_ls.ls("storage://bob/foo", http_backed_storage)
                my_mock.assert_called_with(
                    method="GET",
                    json=None,
                    url="http://127.0.0.1/storage/bob/foo",
                    params="LISTSTATUS",
                    data=None,
                )

    async def test_ls_alice_removes_bob_data_file(self, alice_ls, http_backed_storage):
        with mock.patch(
            "aiohttp.ClientSession.request",
            new=mocked_async_context_manager(empty_response),
        ) as my_mock:
            with mock.patch(
                "neuromation.cli.rc.Config.get_platform_user_name", new="alice"
            ):
                await alice_ls.ls("storage://bob/foo/data.txt/", http_backed_storage)
                my_mock.assert_called_with(
                    method="GET",
                    json=None,
                    url="http://127.0.0.1/storage/bob/foo/data.txt",
                    params="LISTSTATUS",
                    data=None,
                )
