from typing import Callable

import pytest
from aiohttp import web

from neuromation.api import AuthorizationError, Client
from neuromation.api.quota import _QuotaInfo
from tests import _TestServerFactory


_MakeClient = Callable[..., Client]


async def test_quota_get_self(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handle_stats(request: web.Request) -> web.StreamResponse:
        data = {
            "name": request.match_info["name"],
            "jobs": {
                "total_gpu_run_time_minutes": 101,
                "total_non_gpu_run_time_minutes": 102,
            },
            "quota": {
                "total_gpu_run_time_minutes": 201,
                "total_non_gpu_run_time_minutes": 202,
            },
        }
        return web.json_response(data)

    app = web.Application()
    app.router.add_get("/stats/users/{name}", handle_stats)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        quota = await client._quota.get()
        assert quota == _QuotaInfo(
            name=client.username,
            gpu_time_spent=float(101 * 60),
            gpu_time_limit=float(201 * 60),
            cpu_time_spent=float(102 * 60),
            cpu_time_limit=float(202 * 60),
        )


async def test_quota_get_another_user(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handle_stats(request: web.Request) -> web.StreamResponse:
        data = {
            "name": request.match_info["name"],
            "jobs": {
                "total_gpu_run_time_minutes": 101,
                "total_non_gpu_run_time_minutes": 102,
            },
            "quota": {
                "total_gpu_run_time_minutes": 201,
                "total_non_gpu_run_time_minutes": 202,
            },
        }
        return web.json_response(data)

    app = web.Application()
    app.router.add_get("/stats/users/{name}", handle_stats)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        quota = await client._quota.get("another-user")
        assert quota == _QuotaInfo(
            name="another-user",
            gpu_time_spent=float(101 * 60),
            gpu_time_limit=float(201 * 60),
            cpu_time_spent=float(102 * 60),
            cpu_time_limit=float(202 * 60),
        )


async def test_quota_get_no_quota(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handle_stats(request: web.Request) -> web.StreamResponse:
        data = {
            "name": request.match_info["name"],
            "jobs": {
                "total_gpu_run_time_minutes": 101,
                "total_non_gpu_run_time_minutes": 102,
            },
            "quota": {},
        }
        return web.json_response(data)

    app = web.Application()
    app.router.add_get("/stats/users/{name}", handle_stats)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        quota = await client._quota.get()
        assert quota == _QuotaInfo(
            name=client.username,
            gpu_time_spent=float(101 * 60),
            gpu_time_limit=float("inf"),
            cpu_time_spent=float(102 * 60),
            cpu_time_limit=float("inf"),
        )


async def test_quota_get_another_user_not_enough_permissions(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handle_stats(request: web.Request) -> web.StreamResponse:
        name = request.match_info["name"]
        data = {"missing": [{"uri": f"user://{name}", "action": "read"}]}
        return web.json_response(data, status=web.HTTPForbidden.status_code)

    app = web.Application()
    app.router.add_get("/stats/users/{name}", handle_stats)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        with pytest.raises(
            AuthorizationError, match='"uri": "user://another-user", "action": "read"'
        ):
            await client._quota.get("another-user")
