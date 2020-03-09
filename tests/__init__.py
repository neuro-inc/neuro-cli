from typing import Awaitable, Callable

from aiohttp.test_utils import (
    RawTestServer,
    TestClient as _TestClient,
    TestServer as _TestServer,
)
from aiohttp.web import Application, Request, StreamResponse


_TestServerFactory = Callable[[Application], Awaitable[_TestServer]]
_RawTestServerFactory = Callable[
    [Callable[[Request], Awaitable[StreamResponse]]], Awaitable[RawTestServer]
]
_TestClientFactory = Callable[[Application], Awaitable[_TestClient]]
