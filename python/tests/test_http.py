from unittest import mock
from unittest.mock import patch

import aiohttp
import pytest

from neuromation.client.client import ApiClient, TimeoutSettings
from neuromation.client.requests import build
from neuromation.http import FetchError, JsonRequest, fetch, session
from utils import JsonResponse, mocked_async_context_manager


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse({'hello': 'world'})))
@patch('neuromation.client.requests.build')
def test_call(build, loop):
    expected_json = {'a': 'b'}
    expected_params = {'foo': 'bar'}
    expected_url = 'http://test/my'
    expected_data = b'content'
    expected_method = 'GET'
    _session = loop.run_until_complete(session())

    res = loop.run_until_complete(
        fetch(JsonRequest(
                url='/my',
                params=expected_params,
                method=expected_method,
                json=expected_json,
                data=expected_data
            ), _session, 'http://test'))

    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        json=expected_json,
        params=expected_params,
        url=expected_url,
        data=expected_data)

    assert _session._default_headers == {}

    assert res == {'hello': 'world'}


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse({'hello': 'world'})))
@patch('neuromation.client.requests.build')
def test_call_session_with_token(build, loop):
    expected_json = {'a': 'b'}
    expected_params = {'foo': 'bar'}
    expected_url = 'http://test/my'
    expected_data = b'content'
    expected_method = 'GET'
    expected_auth_token = 'test-token-provided'
    _session = loop.run_until_complete(session(token=expected_auth_token))

    res = loop.run_until_complete(
        fetch(JsonRequest(
                url='/my',
                params=expected_params,
                method=expected_method,
                json=expected_json,
                data=expected_data
            ), _session, 'http://test'))

    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        json=expected_json,
        params=expected_params,
        url=expected_url,
        data=expected_data)

    assert 'Authorization' in _session._default_headers
    req_authorization_ = _session._default_headers['Authorization']
    assert req_authorization_ == f'Bearer {expected_auth_token}'

    assert res == {'hello': 'world'}


def test_session_with_timeout_api_client(loop):
    with mock.patch('aiohttp.ClientSession') as runMock:
        timeout = TimeoutSettings(total=1,
                                  connect=2,
                                  sock_connect=3,
                                  sock_read=4)
        ApiClient(url='no-url', token='', timeout=timeout)
        client_timeout = aiohttp.ClientTimeout(
            total=1,
            connect=2,
            sock_connect=3,
            sock_read=4,
        )
        assert runMock.call_count == 1
        args = runMock.call_args_list[0]
        assert args[1]['timeout'] == client_timeout


def test_session_without_timeout_api_client(loop):
    with mock.patch('aiohttp.ClientSession') as runMock:
        timeout = TimeoutSettings(total=5 * 60,
                                  connect=None,
                                  sock_connect=None,
                                  sock_read=None)
        ApiClient(url='no-url', token='', timeout=timeout)
        client_timeout = aiohttp.ClientTimeout(
            total=5 * 60,
            connect=None,
            sock_connect=None,
            sock_read=None,
        )
        assert runMock.call_count == 1
        args = runMock.call_args_list[0]
        assert args[1]['timeout'] == client_timeout


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse(
        json={},
        error=aiohttp.ClientResponseError(
            request_info=None,
            history=None,
            status=500,
            message='ah!')
    )))
def test_fetch(loop):
    _session = loop.run_until_complete(session())

    with pytest.raises(FetchError):
        loop.run_until_complete(
            fetch(
                JsonRequest(
                    method='GET',
                    params=None,
                    url='/foo',
                    data=None,
                    json=None),
                session=_session,
                url='http://foo'))


def test_unknown_request_type():
    with pytest.raises(TypeError):
        build(None)
