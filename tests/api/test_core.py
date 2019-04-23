import ssl
import sys
from typing import Any, AsyncIterator

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
async def api_factory() -> Any:
    @asynccontextmanager
    async def factory(url: URL) -> AsyncIterator[_Core]:
        ssl_context = ssl.SSLContext()
        ssl_context.load_verify_locations(capath=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        api = _Core(connector, url, "token", DEFAULT_TIMEOUT)
        yield api
        await api.close()
        await connector.close()

    yield factory


async def test_raise_for_status_no_error_message(
    aiohttp_server: Any, api_factory: Any
) -> None:
    async def handler(request: web.Request) -> web.Response:
        raise web.HTTPBadRequest()

    app = web.Application()
    app.router.add_get("/test", handler)
    srv = await aiohttp_server(app)

    async with api_factory(srv.make_url("/")) as api:
        with pytest.raises(IllegalArgumentError, match="^400: Bad Request$"):
            async with api.request(method="GET", rel_url=URL("test")):
                pass


async def test_raise_for_status_contains_error_message(
    aiohttp_server: Any, api_factory: Any
) -> None:
    ERROR_MSG = '{"error": "this is the error message"}'

    async def handler(request: web.Request) -> web.Response:
        raise web.HTTPBadRequest(text=ERROR_MSG)

    app = web.Application()
    app.router.add_get("/test", handler)
    srv = await aiohttp_server(app)

    async with api_factory(srv.make_url("/")) as api:
        with pytest.raises(IllegalArgumentError, match=f"^{ERROR_MSG}$"):
            async with api.request(method="GET", rel_url=URL("test")):
                pass
