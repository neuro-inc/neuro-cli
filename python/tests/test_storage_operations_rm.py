from unittest.mock import MagicMock, Mock

import pytest

from neuromation import Storage
from neuromation.cli.command_handlers import PlatformRemoveOperation


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


class TestNormalCases:
    def test_fix_leading_platform_slash(self, mocked_store,
                                        partial_mocked_store):
        PlatformRemoveOperation().remove('storage:data',
                                         partial_mocked_store)
        mocked_store.rm.assert_called_once()
        mocked_store.rm.assert_called_with(path='storage:///data')

    def test_self_principal(self, mocked_store,
                            partial_mocked_store):
        PlatformRemoveOperation().remove('storage://~/data',
                                         partial_mocked_store)
        mocked_store.rm.assert_called_once()
        mocked_store.rm.assert_called_with(path='storage://~/data')

    def test_no_principal(self, mocked_store,
                          partial_mocked_store):
        PlatformRemoveOperation().remove('storage:/data',
                                         partial_mocked_store)
        mocked_store.rm.assert_called_once()
        mocked_store.rm.assert_called_with(path='storage:///data')

    def test_with_principal(self, mocked_store, partial_mocked_store):
        PlatformRemoveOperation().remove('storage://alice/data',
                                         partial_mocked_store)
        mocked_store.rm.assert_called_once()
        mocked_store.rm.assert_called_with(path='storage://alice/data')


class TestInvalidScenarios:

    def test_malformed(self, partial_mocked_store):
        with pytest.raises(ValueError,
                           match=r'Invalid path value.'):
            PlatformRemoveOperation().remove('storage:',
                                             partial_mocked_store)

    def test_local(self, partial_mocked_store):
        with pytest.raises(ValueError,
                           match=r'Path should be '
                                 r'targeting platform storage.'):
            PlatformRemoveOperation().remove('/home/dir',
                                             partial_mocked_store)

    def test_http(self, partial_mocked_store):
        with pytest.raises(ValueError,
                           match=r'Path should be '
                                 r'targeting platform storage.'):
            PlatformRemoveOperation().remove('http:///home/dir',
                                             partial_mocked_store)
