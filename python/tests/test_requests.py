from unittest.mock import patch

import aiohttp
import pytest

from neuromation import requests
from utils import JsonResponse, mocked_async_context_manager


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse({'hello': 'world'})))
@patch('neuromation.requests.route_method')
def test_call(route_method, loop):
    expected_json = {'a': 'b'}
    expected_params = {'foo': 'bar'}
    expected_url = 'http://test/my'
    expected_data = b'content'
    expected_method = 'GET'
    session = loop.run_until_complete(requests.session())

    route_method.return_value = (
        '/my',
        expected_params,
        expected_method,
        expected_json,
        expected_data)
    res = loop.run_until_complete(
        requests.fetch(session, 'http://test', None))

    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        json=expected_json,
        params=expected_params,
        url=expected_url,
        data=expected_data)

    assert res == {'hello': 'world'}


def test_fetch(loop):
    class UnknownRequest(requests.Request):
        pass

    session = loop.run_until_complete(requests.session())
    with pytest.raises(TypeError, match=r'Unknown request type: .*'):
        loop.run_until_complete(
            requests.fetch('http://foo', session, UnknownRequest()))
