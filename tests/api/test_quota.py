from typing import Callable

from aiohttp import web

from neuromation.api import Client
from neuromation.api.quota import QuotaDetails, QuotaInfo
from tests import _TestServerFactory


_MakeClient = Callable[..., Client]


async def test_quota_get(
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
        quota = await client.quota.get()
        assert quota == QuotaInfo(
            name=client.username,
            gpu_details=QuotaDetails(spent_minutes=101, limit_minutes=201),
            cpu_details=QuotaDetails(spent_minutes=102, limit_minutes=202),
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
        quota = await client.quota.get()
        assert quota == QuotaInfo(
            name=client.username,
            gpu_details=QuotaDetails(spent_minutes=101, limit_minutes=None),
            cpu_details=QuotaDetails(spent_minutes=102, limit_minutes=None),
        )
