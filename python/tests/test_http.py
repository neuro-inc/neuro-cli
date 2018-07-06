from unittest.mock import patch

import aiohttp

from neuromation.http import Request, fetch, session
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
        fetch(_session, 'http://test', Request(
                url='/my',
                params=expected_params,
                method=expected_method,
                json=expected_json,
                data=expected_data
            )))

    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        json=expected_json,
        params=expected_params,
        url=expected_url,
        data=expected_data)

    assert res == {'hello': 'world'}


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse(
        aiohttp.ClientResponseError(
            request_info=None,
            history=None,
            status=200,
            message='ah!')
    )))
def test_fetch(loop):
    _session = loop.run_until_complete(session())
    loop.run_until_complete(
        fetch(
            session=_session,
            url='http://foo',
            request=Request(
                method='GET',
                params=None,
                url='/foo',
                data=None,
                json=None
            )))
