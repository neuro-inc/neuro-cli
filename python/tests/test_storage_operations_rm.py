from unittest.mock import MagicMock, Mock, patch

import aiohttp
import pytest

from neuromation import Storage
from neuromation.cli.command_handlers import PlatformRemoveOperation
from tests.utils import PlainResponse, mocked_async_context_manager


@pytest.fixture()
def mocked_store(loop):
    my_mock = MagicMock(Storage('no-url', 'no-token', loop=loop))
    my_mock.__enter__ = Mock(return_value=my_mock)
    my_mock.__exit__ = Mock(return_value=False)
    return my_mock


@pytest.fixture()
def partial_mocked_store(mocked_store):
    def partial_mocked_store_func():
        return mocked_store
    return partial_mocked_store_func


@pytest.fixture()
def alice_rm():
    return PlatformRemoveOperation('alice')


@pytest.fixture
def storage(loop):
    storage = Storage(url='http://127.0.0.1',
                      token='test-token-for-storage',
                      loop=loop)
    return storage


@pytest.fixture()
def http_backed_storage(storage):
    def partial_mocked_store():
        return storage
    return partial_mocked_store


class TestNormalCases:

    def test_fix_leading_platform_slash(self, alice_rm, partial_mocked_store):
        alice_rm.remove('storage:data', partial_mocked_store)
        partial_mocked_store().rm.assert_called_once()
        partial_mocked_store().rm.assert_called_with(path='/alice/data')

    def test_self_principal(self, alice_rm, partial_mocked_store):
        alice_rm.remove('storage://~/data', partial_mocked_store)
        partial_mocked_store().rm.assert_called_once()
        partial_mocked_store().rm.assert_called_with(path='/alice/data')

    def test_no_principal(self, alice_rm, partial_mocked_store):
        alice_rm.remove('storage:/data', partial_mocked_store)
        partial_mocked_store().rm.assert_called_once()
        partial_mocked_store().rm.assert_called_with(path='/alice/data')

    def test_with_principal(self, alice_rm, partial_mocked_store):
        alice_rm.remove('storage://alice/data', partial_mocked_store)
        partial_mocked_store().rm.assert_called_once()
        partial_mocked_store().rm.assert_called_with(path='/alice/data')

    def test_with_principal_file(self, alice_rm, partial_mocked_store):
        alice_rm.remove('storage://alice/data/foo.txt', partial_mocked_store)
        partial_mocked_store().rm.assert_called_once()
        partial_mocked_store().rm.assert_called_with(
            path='/alice/data/foo.txt')

    def test_with_principal_bob_file(self, alice_rm, partial_mocked_store):
        alice_rm.remove('storage://bob/data/foo.txt', partial_mocked_store)
        partial_mocked_store().rm.assert_called_once()
        partial_mocked_store().rm.assert_called_with(path='/bob/data/foo.txt')

    def test_with_principal_file_ensure_slash(self,
                                              alice_rm,
                                              partial_mocked_store):
        alice_rm.remove('storage://alice/data/foo.txt/', partial_mocked_store)
        partial_mocked_store().rm.assert_called_once()
        partial_mocked_store().rm.assert_called_with(
            path='/alice/data/foo.txt')


class TestInvalidScenarios:

    def test_malformed(self, alice_rm, partial_mocked_store):
        with pytest.raises(ValueError,
                           match=r'Invalid path value.'):
            alice_rm.remove('storage:', partial_mocked_store)

    def test_local(self, alice_rm, partial_mocked_store):
        with pytest.raises(ValueError,
                           match=r'Path should be '
                                 r'targeting platform storage.'):
            alice_rm.remove('/home/dir', partial_mocked_store)

    def test_http(self, alice_rm, partial_mocked_store):
        with pytest.raises(ValueError,
                           match=r'Path should be '
                                 r'targeting platform storage.'):
            alice_rm.remove('http:///home/dir', partial_mocked_store)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(PlainResponse(text='')))
@patch(
    'neuromation.cli.rc.Config.get_platform_user_name',
    new='alice'
)
def test_rm_alice_no_user(alice_rm, http_backed_storage):
    alice_rm.remove('storage:///foo', http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method='DELETE',
        json=None,
        url='http://127.0.0.1/storage/alice/foo',
        params=None,
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(PlainResponse(text='')))
@patch(
    'neuromation.cli.rc.Config.get_platform_user_name',
    new='alice'
)
def test_rm_alice_tilde_user(alice_rm, http_backed_storage):
    alice_rm.remove('storage://~/foo', http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method='DELETE',
        json=None,
        url='http://127.0.0.1/storage/alice/foo',
        params=None,
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(PlainResponse(text='')))
@patch(
    'neuromation.cli.rc.Config.get_platform_user_name',
    new='alice'
)
def test_rm_alice_omitted_user(alice_rm, http_backed_storage):
    alice_rm.remove('storage:/foo', http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method='DELETE',
        json=None,
        url='http://127.0.0.1/storage/alice/foo',
        params=None,
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(PlainResponse(text='')))
@patch(
    'neuromation.cli.rc.Config.get_platform_user_name',
    new='alice'
)
def test_rm_alice_omitted_user_no_leading_slash(alice_rm,
                                                http_backed_storage):
    alice_rm.remove('storage:foo', http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method='DELETE',
        json=None,
        url='http://127.0.0.1/storage/alice/foo',
        params=None,
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(PlainResponse(text='')))
@patch(
    'neuromation.cli.rc.Config.get_platform_user_name',
    new='alice'
)
def test_rm_alice_removes_bob_data(alice_rm, http_backed_storage):
    alice_rm.remove('storage://bob/foo', http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method='DELETE',
        json=None,
        url='http://127.0.0.1/storage/bob/foo',
        params=None,
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(PlainResponse(text='')))
@patch(
    'neuromation.cli.rc.Config.get_platform_user_name',
    new='alice'
)
def test_rm_alice_removes_bob_data_file(alice_rm, http_backed_storage):
    alice_rm.remove('storage://bob/foo/data.txt/', http_backed_storage)
    aiohttp.ClientSession.request.assert_called_with(
        method='DELETE',
        json=None,
        url='http://127.0.0.1/storage/bob/foo/data.txt',
        params=None,
        data=None)
