from typing import List
from unittest.mock import patch

import aiohttp
from aiohttp import web
from dataclasses import dataclass

from neuromation.requests import Request, fetch
from utils import mocked_async_context_manager


def build_request(method):
    @dataclass
    class Nested:
        values: List[str]

    @dataclass
    class MyRequest(Request):
        value: str
        nested: Nested

        def __post_init__(self):
            super().__init__(route='/my', method=method)

    return MyRequest(value='foo', nested=Nested(values=list('abc')))


@patch(
    'aiohttp.ClientSession.get',
    new=mocked_async_context_manager(web.json_response({'method': 'GET'})))
@patch(
    'aiohttp.ClientSession.post',
    new=mocked_async_context_manager(web.json_response({'method': 'POST'})))
def test_call(request, loop):
    expected_json = {
                'value': 'foo',
                'nested': {
                    'values': ['a', 'b', 'c']
                }
            }
    expected_url = 'http://test/my'

    res = loop.run_until_complete(fetch('http://test', build_request('GET')))

    aiohttp.ClientSession.get.assert_called_with(
        json=expected_json,
        url=expected_url)
    assert res == {'method': 'GET'}

    res = loop.run_until_complete(fetch('http://test', build_request('POST')))
    aiohttp.ClientSession.get.assert_called_with(
        json=expected_json,
        url=expected_url)
    assert res == {'method': 'POST'}
