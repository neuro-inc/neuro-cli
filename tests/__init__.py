from typing import Awaitable, Callable

from aiohttp.test_utils import RawTestServer, TestServer as _TestServer
from aiohttp.web import Application, Request, StreamResponse


_TestServerFactory = Callable[[Application], Awaitable[_TestServer]]
_RawTestServerFactory = Callable[
    [Callable[[Request], Awaitable[StreamResponse]]], Awaitable[RawTestServer]
]
