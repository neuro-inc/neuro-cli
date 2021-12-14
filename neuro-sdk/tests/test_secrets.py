import base64
from typing import Callable

from aiohttp import web

from neuro_sdk import Client, Secret

from tests import _TestServerFactory

_MakeClient = Callable[..., Client]


async def test_list(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handler(request: web.Request) -> web.Response:
        return web.json_response(
            [
                {"key": "name1", "owner": "test"},
                {"key": "name2", "owner": "test", "org_name": "test-org"},
            ]
        )

    app = web.Application()
    app.router.add_get("/secrets", handler)

    srv = await aiohttp_server(app)

    ret = []

    async with make_client(srv.make_url("/")) as client:
        async with client.secrets.list() as it:
            async for s in it:
                ret.append(s)

    assert ret == [
        Secret(key="name1", owner="test", cluster_name="default", org_name=None),
        Secret(key="name2", owner="test", cluster_name="default", org_name="test-org"),
    ]


async def test_add(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handler(request: web.Request) -> web.Response:
        data = await request.json()
        assert data == {
            "key": "name",
            "value": base64.b64encode(b"data").decode("ascii"),
            "org_name": None,
        }
        raise web.HTTPCreated

    app = web.Application()
    app.router.add_post("/secrets", handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        await client.secrets.add("name", b"data")


async def test_add_with_org(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handler(request: web.Request) -> web.Response:
        data = await request.json()
        assert data == {
            "key": "name",
            "value": base64.b64encode(b"data").decode("ascii"),
            "org_name": "test-org",
        }
        raise web.HTTPCreated

    app = web.Application()
    app.router.add_post("/secrets", handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        await client.secrets.add("name", b"data", org_name="test-org")


async def test_rm(aiohttp_server: _TestServerFactory, make_client: _MakeClient) -> None:
    async def handler(request: web.Request) -> web.Response:
        assert request.match_info["key"] == "name"
        raise web.HTTPNoContent

    app = web.Application()
    app.router.add_delete("/secrets/{key}", handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        await client.secrets.rm("name")


async def test_rm_with_org(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handler(request: web.Request) -> web.Response:
        assert request.match_info["key"] == "name"
        assert request.query.get("org_name") == "test-org"
        raise web.HTTPNoContent

    app = web.Application()
    app.router.add_delete("/secrets/{key}", handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        await client.secrets.rm("name", org_name="test-org")
