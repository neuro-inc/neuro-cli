from io import BytesIO
from unittest.mock import patch

import aiohttp
import pytest

from neuromation import client
from utils import BinaryResponse, JsonResponse, mocked_async_context_manager


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse(
        {},
        error=aiohttp.ClientResponseError(
            request_info=None,
            history=None,
            status=500,
            message='ah!')
    )))
def test_error(storage):
    with pytest.raises(client.ApiError) as exc:
        storage.rm(path='blah')
    assert exc.value.args == ('ah!',)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse(
        [
            {
                'path': 'foo',
                'size': 1024,
                'type': 'FILE'
            },
            {
                'path': 'bar',
                'size': 4*1024,
                'type': 'DIR'
            }
        ]
    )))
def test_ls(storage):
    assert storage.ls(path='/home/dir') == [
        client.FileStatus(path='foo', size=1024, type='FILE'),
        client.FileStatus(path='bar', size=4*1024, type='DIR')
    ]

    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        url='http://127.0.0.1/storage/home/dir',
        params='LISTSTATUS',
        data=None,
        json=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(BinaryResponse(data=None)))
def test_mkdirs(storage):
    assert storage.mkdirs(root='home', paths=['foo', 'bar']) == ['foo', 'bar']
    aiohttp.ClientSession.request.assert_called_with(
        method='PUT',
        json=['foo', 'bar'],
        url='http://127.0.0.1/storage/home',
        params='MKDIRS',
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(BinaryResponse(data=None)))
def test_rm(storage):
    assert storage.rm(path='foo')
    aiohttp.ClientSession.request.assert_called_with(
        method='DELETE',
        json=None,
        url='http://127.0.0.1/storage/foo',
        params=None,
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(BinaryResponse(data=None)))
def test_create(storage):
    data = BytesIO(b'bar')
    assert storage.create(path='foo', data=data)
    aiohttp.ClientSession.request.assert_called_with(
        method='PUT',
        url='http://127.0.0.1/storage/foo',
        params=None,
        data=data,
        json=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(BinaryResponse(data=b'bar')))
def test_open(storage):
    assert storage.open(path='foo').read() == b'bar'
    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        url='http://127.0.0.1/storage/foo',
        params=None,
        json=None,
        data=None)
