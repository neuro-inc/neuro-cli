import functools
from unittest.mock import MagicMock, Mock, patch

import aiohttp
import pytest

from neuromation import Storage
from neuromation.cli.command_handlers import PlatformRemoveOperation
from tests.utils import PlainResponse, mocked_async_context_manager


@pytest.fixture(scope='function')
def mocked_store(loop):
    my_mock = MagicMock(Storage('no-url', 'no-token', loop=loop))
    my_mock.__enter__ = Mock(return_value=my_mock)
    my_mock.__exit__ = Mock(return_value=False)
    # my_mock.mkdir = Mock(return_value=False)
    # my_mock.ls = Mock(return_value=False)
    return my_mock


@pytest.fixture(scope='function')
def partial_mocked_store(mocked_store):
    def partial_mocked_store():
        return mocked_store
    return partial_mocked_store


@pytest.fixture
def storage_2(loop):
    storage = Storage(url='http://127.0.0.1', token='test-token-for-storage', loop=loop)
    return storage


@pytest.fixture()
def partial_mocked_store_http(storage_2):
    def partial_mocked_store():
        return storage_2
    return partial_mocked_store


class TestNormalCases:
    @pytest.parametrized
    def test_fix_leading_platform_slash(self, mocked_store,
                                        partial_mocked_store):
        PlatformRemoveOperation('alice').remove('storage:data',
                                         partial_mocked_store)
        mocked_store.rm.assert_called_once()
        mocked_store.rm.assert_called_with(path='/alice/data')

    def test_self_principal(self, mocked_store,
                            partial_mocked_store):
        PlatformRemoveOperation().remove('alice', 'storage://~/data',
                                         partial_mocked_store)
        mocked_store.rm.assert_called_once()
        mocked_store.rm.assert_called_with(path='/alice/data')

    def test_no_principal(self, mocked_store,
                          partial_mocked_store):
        PlatformRemoveOperation().remove('alice', 'storage:/data',
                                         partial_mocked_store)
        mocked_store.rm.assert_called_once()
        mocked_store.rm.assert_called_with(path='/alice/data')

    def test_with_principal(self, mocked_store, partial_mocked_store):
        PlatformRemoveOperation().remove('alice', 'storage://alice/data',
                                         partial_mocked_store)
        mocked_store.rm.assert_called_once()
        mocked_store.rm.assert_called_with(path='/alice/data')


class TestInvalidScenarios:

    def test_malformed(self, partial_mocked_store):
        with pytest.raises(ValueError,
                           match=r'Invalid path value.'):
            PlatformRemoveOperation().remove('alice', 'storage:',
                                             partial_mocked_store)

    def test_local(self, partial_mocked_store):
        with pytest.raises(ValueError,
                           match=r'Path should be '
                                 r'targeting platform storage.'):
            PlatformRemoveOperation().remove('alice', '/home/dir',
                                             partial_mocked_store)

    def test_http(self, partial_mocked_store):
        with pytest.raises(ValueError,
                           match=r'Path should be '
                                 r'targeting platform storage.'):
            PlatformRemoveOperation().remove('alice', 'http:///home/dir',
                                             partial_mocked_store)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(PlainResponse(text='')))
@patch(
    'neuromation.cli.rc.Config.get_platform_user_name',
    new='alice'
)
def test_rm_alice_no_user(partial_mocked_store_http):
    PlatformRemoveOperation().remove('alice', 'storage:///foo', partial_mocked_store_http)
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
def test_rm_alice_tilde_user(partial_mocked_store_http):
    PlatformRemoveOperation().remove('alice', 'storage://~/foo', partial_mocked_store_http)
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
def test_rm_alice_omitted_user(partial_mocked_store_http):
    PlatformRemoveOperation().remove('alice', 'storage:/foo', partial_mocked_store_http)
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
def test_rm_alice_omitted_user_no_leading_slash(partial_mocked_store_http):
    PlatformRemoveOperation().remove('alice', 'storage:foo', partial_mocked_store_http)
    aiohttp.ClientSession.request.assert_called_with(
        method='DELETE',
        json=None,
        url='http://127.0.0.1/storage/alice/foo',
        params=None,
        data=None)
