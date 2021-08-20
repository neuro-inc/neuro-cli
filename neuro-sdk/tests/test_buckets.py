from datetime import datetime, timedelta
from typing import Callable

from aiohttp import web

from neuro_sdk import Bucket, Client, Cluster

from tests import _TestServerFactory

_MakeClient = Callable[..., Client]


async def test_list(
    aiohttp_server: _TestServerFactory,
    make_client: _MakeClient,
    cluster_config: Cluster,
) -> None:
    created_at = datetime.now() - timedelta(days=1)

    async def handler(request: web.Request) -> web.Response:
        return web.json_response(
            [
                {
                    "id": "bucket-1",
                    "owner": "user",
                    "name": None,
                    "provider": "aws",
                    "created_at": created_at.isoformat(),
                },
                {
                    "id": "bucket-2",
                    "owner": "user",
                    "name": "test-bucket",
                    "provider": "aws",
                    "created_at": created_at.isoformat(),
                },
            ]
        )

    app = web.Application()
    app.router.add_get("/buckets/buckets", handler)

    srv = await aiohttp_server(app)

    ret = []

    async with make_client(srv.make_url("/")) as client:
        async with client.buckets.list() as it:
            async for s in it:
                ret.append(s)

    assert ret == [
        Bucket(
            id="bucket-1",
            owner="user",
            cluster_name=cluster_config.name,
            name=None,
            created_at=created_at,
            provider=Bucket.Provider.AWS,
        ),
        Bucket(
            id="bucket-2",
            owner="user",
            cluster_name=cluster_config.name,
            name="test-bucket",
            created_at=created_at,
            provider=Bucket.Provider.AWS,
        ),
    ]


async def test_add(
    aiohttp_server: _TestServerFactory,
    make_client: _MakeClient,
    cluster_config: Cluster,
) -> None:
    created_at = datetime.now()

    async def handler(request: web.Request) -> web.Response:
        data = await request.json()
        assert data == {
            "name": "test-bucket",
        }
        return web.json_response(
            {
                "id": "bucket-1",
                "owner": "user",
                "name": "test-bucket",
                "created_at": created_at.isoformat(),
                "provider": "aws",
            }
        )

    app = web.Application()
    app.router.add_post("/buckets/buckets", handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        bucket = await client.buckets.create(name="test-bucket")
        assert bucket == Bucket(
            id="bucket-1",
            owner="user",
            cluster_name=cluster_config.name,
            name="test-bucket",
            created_at=created_at,
            provider=Bucket.Provider.AWS,
        )


async def test_get(
    aiohttp_server: _TestServerFactory,
    make_client: _MakeClient,
    cluster_config: Cluster,
) -> None:
    created_at = datetime.now()

    async def handler(request: web.Request) -> web.Response:
        assert request.match_info["key"] == "name"
        return web.json_response(
            {
                "id": "bucket-1",
                "owner": "user",
                "name": "name",
                "provider": "aws",
                "created_at": created_at.isoformat(),
            }
        )

    app = web.Application()
    app.router.add_get("/buckets/buckets/{key}", handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        bucket = await client.buckets.get("name")
        assert bucket == Bucket(
            id="bucket-1",
            owner="user",
            cluster_name=cluster_config.name,
            name="name",
            created_at=created_at,
            provider=Bucket.Provider.AWS,
        )


async def test_rm(aiohttp_server: _TestServerFactory, make_client: _MakeClient) -> None:
    async def handler(request: web.Request) -> web.Response:
        assert request.match_info["key"] == "name"
        raise web.HTTPNoContent

    app = web.Application()
    app.router.add_delete("/buckets/buckets/{key}", handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        await client.buckets.rm("name")
