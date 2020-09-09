from typing import Callable

from aiohttp import web

from neuromation.api import Client, Cluster, Disk
from tests import _TestServerFactory


_MakeClient = Callable[..., Client]


async def test_list(
    aiohttp_server: _TestServerFactory,
    make_client: _MakeClient,
    cluster_config: Cluster,
) -> None:
    async def handler(request: web.Request) -> web.Response:
        return web.json_response(
            [
                {"id": "disk-1", "storage": 500, "owner": "user", "status": "Ready"},
                {"id": "disk-2", "storage": 600, "owner": "user", "status": "Pending"},
            ]
        )

    app = web.Application()
    app.router.add_get("/disk", handler)

    srv = await aiohttp_server(app)

    ret = []

    async with make_client(srv.make_url("/")) as client:
        async for s in client.disks.list():
            ret.append(s)

    assert ret == [
        Disk(
            id="disk-1",
            storage=500,
            owner="user",
            status=Disk.Status.READY,
            cluster_name=cluster_config.name,
        ),
        Disk(
            id="disk-2",
            storage=600,
            owner="user",
            status=Disk.Status.PENDING,
            cluster_name=cluster_config.name,
        ),
    ]


async def test_add(
    aiohttp_server: _TestServerFactory,
    make_client: _MakeClient,
    cluster_config: Cluster,
) -> None:
    async def handler(request: web.Request) -> web.Response:
        data = await request.json()
        assert data == {
            "storage": 500,
        }
        return web.json_response(
            {"id": "disk-1", "storage": 500, "owner": "user", "status": "Ready"},
        )

    app = web.Application()
    app.router.add_post("/disk", handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        disk = await client.disks.create(500)
        assert disk == Disk(
            id="disk-1",
            storage=500,
            owner="user",
            status=Disk.Status.READY,
            cluster_name=cluster_config.name,
        )


async def test_get(
    aiohttp_server: _TestServerFactory,
    make_client: _MakeClient,
    cluster_config: Cluster,
) -> None:
    async def handler(request: web.Request) -> web.Response:
        assert request.match_info["key"] == "name"
        return web.json_response(
            {"id": "disk-1", "storage": 500, "owner": "user", "status": "Ready"},
        )

    app = web.Application()
    app.router.add_get("/disk/{key}", handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        disk = await client.disks.get("name")
        assert disk == Disk(
            id="disk-1",
            storage=500,
            owner="user",
            status=Disk.Status.READY,
            cluster_name=cluster_config.name,
        )


async def test_rm(aiohttp_server: _TestServerFactory, make_client: _MakeClient) -> None:
    async def handler(request: web.Request) -> web.Response:
        assert request.match_info["key"] == "name"
        raise web.HTTPNoContent

    app = web.Application()
    app.router.add_delete("/disk/{key}", handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        await client.disks.rm("name")
