import os
from unittest.mock import MagicMock, Mock
from urllib.parse import urlparse

import pytest

from neuromation import Storage
from neuromation.cli.command_handlers import (CopyOperation,
                                              PlatformListDirOperation,
                                              PlatformMakeDirOperation)
from neuromation.client import FileStatus


def test_invalid_scheme_combinations():
    with pytest.raises(ValueError, match=r'schemes required'):
        CopyOperation.create('file', 'file', False)

    with pytest.raises(ValueError, match=r'schemes required'):
        CopyOperation.create('storage', 'storage', False)

    with pytest.raises(ValueError, match=r'schemes required'):
        CopyOperation.create('storage', 'abrakadabra', False)

    with pytest.raises(ValueError, match=r'schemes required'):
        CopyOperation.create('file', 'abrakadabra', False)

    with pytest.raises(ValueError, match=r'schemes required'):
        CopyOperation.create('abrakadabra', 'abrakadabra', False)


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


def test_ls(mocked_store, partial_mocked_store):
    PlatformListDirOperation().ls('/home/dir', partial_mocked_store)

    mocked_store.ls.assert_called_once()
    mocked_store.ls.assert_called_with(path='/home/dir')


def test_mkdir(mocked_store, partial_mocked_store):
    PlatformMakeDirOperation().mkdir('/home/dir', partial_mocked_store)

    mocked_store.mkdirs.assert_called_once()
    mocked_store.mkdirs.assert_called_with(path='/home/dir')


# Platform TO Local File System Non Recursive SET
# ARGS
#   src == (dir / file / does not exists)
#   dst == (dir / file / not exists parent dir)
# To test
#   (file, dir)       --> name of a file appended to dest_dir
#   (not exists, dir) --> FAIL
#   (dir, dir)        --> FAIL

def test_copy_local_to_platform_non_recursive_exist_exist_target_is_dir(
        mocked_store, partial_mocked_store, monkeypatch):
    def ls(path):
        if path == '/existing' or path == '/existing/':
            return [FileStatus("my_file.txt", 100, "FILE")]
        return [FileStatus("my_file2.txt", 100, "FILE")]

    def exists_func(src):
        return '/existing/dir/' == src

    def is_dir_func(src):
        return '/existing/dir/' == src

    monkeypatch.setattr(os.path, 'exists', exists_func)
    monkeypatch.setattr(os.path, 'isdir', is_dir_func)
    mocked_store.ls = ls
    transfer_mock = Mock()

    op = CopyOperation.create('storage', 'file', False)
    op.copy_file = transfer_mock
    op.copy(urlparse('storage:///existing/my_file.txt'),
            urlparse('file:///existing/dir/'), partial_mocked_store)

    transfer_mock.assert_called_once()
    transfer_mock.assert_called_with('/existing/my_file.txt',
                                     '/existing/dir/my_file.txt',
                                     partial_mocked_store)


def test_copy_local_to_platform_non_recursive_not_exist_exist_target_is_dir(
        mocked_store, partial_mocked_store, monkeypatch):
    def ls(path):
        if path == '/existing' or path == '/existing/':
            return [FileStatus("my_file2.txt", 100, "FILE")]
        return [FileStatus("my_file.txt", 100, "FILE")]

    def exists_func(src):
        return '/existing/dir/' == src

    def is_dir_func(src):
        return '/existing/dir/' == src

    monkeypatch.setattr(os.path, 'exists', exists_func)
    monkeypatch.setattr(os.path, 'isdir', is_dir_func)
    mocked_store.ls = ls
    transfer_mock = Mock()

    op = CopyOperation.create('storage', 'file', False)
    op.copy_file = transfer_mock
    with pytest.raises(ValueError):
        op.copy(urlparse('storage:///existing/my_file.txt'),
                urlparse('file:///existing/dir/'), partial_mocked_store)
    transfer_mock.assert_not_called()


def test_copy_local_to_platform_non_recursive_dir_exist_exist_target_is_dir(
        mocked_store, partial_mocked_store, monkeypatch):
    def ls(path):
        if path == '/existing' or path == '/existing/':
            return [FileStatus("my_file.txt", 0, "DIRECTORY")]
        return [FileStatus("my_file.txt", 100, "FILE")]

    def exists_func(src):
        return '/existing/dir/' == src

    def is_dir_func(src):
        return '/existing/dir/' == src

    monkeypatch.setattr(os.path, 'exists', exists_func)
    monkeypatch.setattr(os.path, 'isdir', is_dir_func)
    mocked_store.ls = ls
    transfer_mock = Mock()

    op = CopyOperation.create('storage', 'file', False)
    op.copy_file = transfer_mock
    with pytest.raises(ValueError):
        op.copy(urlparse('storage:///existing/my_file.txt'),
                urlparse('file:///existing/dir/'), partial_mocked_store)
    transfer_mock.assert_not_called()


def test_copy_local_to_platform_non_recursive_exist_exist_target_is_file(
        mocked_store, partial_mocked_store, monkeypatch):
    def ls(path):
        return [FileStatus("my_file.txt", 100, "FILE")]

    def exists_func(src):
        return '/existing/dir/' != src

    def is_dir_func(src):
        return '/existing/dir/' != src

    monkeypatch.setattr(os.path, 'exists', exists_func)
    monkeypatch.setattr(os.path, 'isdir', is_dir_func)
    mocked_store.ls = ls
    transfer_mock = Mock()

    op = CopyOperation.create('storage', 'file', False)
    op.copy_file = transfer_mock
    op.copy(urlparse('storage:///existing/my_file.txt'),
            urlparse('file:///existing/dir/'), partial_mocked_store)

    transfer_mock.assert_called_once()
    transfer_mock.assert_called_with('/existing/my_file.txt',
                                     '/existing/dir', partial_mocked_store)
