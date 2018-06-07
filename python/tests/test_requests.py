from typing import List
from unittest.mock import patch

import aiohttp
import pytest
from aiohttp import web
from dataclasses import dataclass, replace

from neuromation import requests
from utils import mocked_async_context_manager


def build_request(method):
    @dataclass
    class Nested:
        values: List[str]

    @dataclass
    class MyRequest(requests.Request):
        value: str
        nested: Nested
        route='/my'
        method='GET'

    request = MyRequest(value='foo', nested=Nested(values=list('abc')))
    request.method = method

    return request


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(web.json_response({'hello': 'world'})))
@patch('neuromation.requests.route_method')
def test_call(route_method, loop):
    expected_json = {
                'value': 'foo',
                'nested': {
                    'values': ['a', 'b', 'c']
                }
            }
    expected_url = 'http://test/my'

    session = loop.run_until_complete(requests.session())

    request = build_request('GET')
    route_method.return_value = ('/my', 'GET')
    res = loop.run_until_complete(requests.fetch(session, 'http://test', request))

    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        json=expected_json,
        url=expected_url)
    assert res == {'hello': 'world'}

    request = build_request('POST')
    route_method.return_value = ('/my', 'POST')
    res = loop.run_until_complete(requests.fetch(session, 'http://test', request))
    aiohttp.ClientSession.request.assert_called_with(
        method='POST',
        json=expected_json,
        url=expected_url)
    assert res == {'hello': 'world'}


def test_fetch(loop):
    class UnknownRequest(requests.Request):
        pass

    session = loop.run_until_complete(requests.session())
    with pytest.raises(TypeError, match=r'Unknown request type: .*'):
        loop.run_until_complete(requests.fetch('http://foo', session, UnknownRequest()))
