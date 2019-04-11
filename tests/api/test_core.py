import ssl
import sys

import aiohttp
import certifi
import pytest
from aiohttp import web
from yarl import URL

from neuromation.api.core import DEFAULT_TIMEOUT, IllegalArgumentError, _Core


if sys.version_info >= (3, 7):
    from contextlib import asynccontextmanager
else:
    from async_generator import asynccontextmanager


@pytest.fixture
async def api_factory():
    @asynccontextmanager
    async def factory(url):
        ssl_context = ssl.SSLContext()
        ssl_context.load_verify_locations(capath=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        api = _Core(connector, url, "token", DEFAULT_TIMEOUT)
        yield api
        await api.close()
        await connector.close()

    yield factory


async def test_raise_for_status_no_error_message(aiohttp_server, api_factory):
    async def handler(request):
        raise web.HTTPBadRequest()

    app = web.Application()
    app.router.add_get("/test", handler)
    srv = await aiohttp_server(app)

    async with api_factory(srv.make_url("/")) as api:
        with pytest.raises(IllegalArgumentError, match="^400: Bad Request$"):
            async with api.request(method="GET", rel_url=URL("test")):
                pass


async def test_raise_for_status_contains_error_message(aiohttp_server, api_factory):
    ERROR_MSG = '{"error": "this is the error message"}'

    async def handler(request):
        raise web.HTTPBadRequest(text=ERROR_MSG)

    app = web.Application()
    app.router.add_get("/test", handler)
    srv = await aiohttp_server(app)

    async with api_factory(srv.make_url("/")) as api:
        with pytest.raises(IllegalArgumentError, match=f"^{ERROR_MSG}$"):
            async with api.request(method="GET", rel_url=URL("test")):
                pass
