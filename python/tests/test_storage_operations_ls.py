from unittest.mock import patch

import aiohttp
import pytest

from neuromation.cli.command_handlers import PlatformListDirOperation
from tests.utils import JsonResponse, mocked_async_context_manager


@pytest.fixture()
def alice_ls():
    return PlatformListDirOperation('alice')


class TestNormalCases:

    def test_list_users(self, alice_ls, partial_mocked_store):
        alice_ls.ls('storage://', partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path='/')

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

    def test_fix_leading_platform_slash(self, alice_ls, partial_mocked_store):
        alice_ls.ls('storage:data', partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path='/alice/data')

    def test_self_principal(self, alice_ls, partial_mocked_store):
        alice_ls.ls('storage://~/data', partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path='/alice/data')

    def test_no_principal(self, alice_ls, partial_mocked_store):
        alice_ls.ls('storage:/data', partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path='/alice/data')

    def test_with_principal(self, alice_ls, partial_mocked_store):
        alice_ls.ls('storage://alice/data', partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path='/alice/data')

    def test_with_principal_file(self, alice_ls, partial_mocked_store):
        alice_ls.ls('storage://alice/data/foo.txt', partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(
            path='/alice/data/foo.txt')

    def test_with_principal_bob_file(self, alice_ls, partial_mocked_store):
        alice_ls.ls('storage://bob/data/foo.txt', partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path='/bob/data/foo.txt')

    def test_with_principal_file_ensure_slash(self,
                                              alice_ls,
                                              partial_mocked_store):
        alice_ls.ls('storage://alice/data/foo.txt/', partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(
            path='/alice/data/foo.txt')

    def test_list_root(self, alice_ls, partial_mocked_store):
        alice_ls.ls('storage:', partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path='/alice')

    def test_list_root_2(self, alice_ls, partial_mocked_store):
        alice_ls.ls('storage:/', partial_mocked_store)
        partial_mocked_store().ls.assert_called_once()
        partial_mocked_store().ls.assert_called_with(path='/alice')


class TestInvalidScenarios:

    def test_local(self, alice_ls, partial_mocked_store):
        with pytest.raises(ValueError,
                           match=r'Path should be '
                                 r'targeting platform storage.'):
            alice_ls.ls('/home/dir', partial_mocked_store)

    def test_http(self, alice_ls, partial_mocked_store):
        with pytest.raises(ValueError,
                           match=r'Path should be '
                                 r'targeting platform storage.'):
            alice_ls.ls('http:///home/dir', partial_mocked_store)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse({})))
@patch(
    'neuromation.cli.rc.Config.get_platform_user_name',
    new='alice'
)
def test_ls_alice_no_user(alice_ls, http_backed_storage):
    alice_ls.ls('storage:///foo', http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        json=None,
        url='http://127.0.0.1/storage/alice/foo',
        params='LISTSTATUS',
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse({})))
@patch(
    'neuromation.cli.rc.Config.get_platform_user_name',
    new='alice'
)
def test_ls_alice_tilde_user(alice_ls, http_backed_storage):
    alice_ls.ls('storage://~/foo', http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        json=None,
        url='http://127.0.0.1/storage/alice/foo',
        params='LISTSTATUS',
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse({})))
@patch(
    'neuromation.cli.rc.Config.get_platform_user_name',
    new='alice'
)
def test_ls_alice_omitted_user(alice_ls, http_backed_storage):
    alice_ls.ls('storage:/foo', http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        json=None,
        url='http://127.0.0.1/storage/alice/foo',
        params='LISTSTATUS',
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse({})))
@patch(
    'neuromation.cli.rc.Config.get_platform_user_name',
    new='alice'
)
def test_ls_alice_omitted_user_no_leading_slash(alice_ls,
                                                http_backed_storage):
    alice_ls.ls('storage:foo', http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        json=None,
        url='http://127.0.0.1/storage/alice/foo',
        params='LISTSTATUS',
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse({})))
@patch(
    'neuromation.cli.rc.Config.get_platform_user_name',
    new='alice'
)
def test_ls_alice_removes_bob_data(alice_ls, http_backed_storage):
    alice_ls.ls('storage://bob/foo', http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        json=None,
        url='http://127.0.0.1/storage/bob/foo',
        params='LISTSTATUS',
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse({})))
@patch(
    'neuromation.cli.rc.Config.get_platform_user_name',
    new='alice'
)
def test_ls_alice_removes_bob_data_file(alice_ls, http_backed_storage):
    alice_ls.ls('storage://bob/foo/data.txt/', http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        json=None,
        url='http://127.0.0.1/storage/bob/foo/data.txt',
        params='LISTSTATUS',
        data=None)
