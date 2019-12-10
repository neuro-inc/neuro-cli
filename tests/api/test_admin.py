from typing import Callable

from aiohttp import web

from neuromation.api import Client
from neuromation.api.admin import _ClusterUser, _ClusterUserRoleType
from tests import _TestServerFactory


_MakeClient = Callable[..., Client]


async def test_list_cluster_users(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handle_list_cluster_user(request: web.Request) -> web.StreamResponse:
        data = [
            {"user_name": "denis", "role": "admin"},
            {"user_name": "andrew", "role": "manager"},
            {"user_name": "ivan", "role": "user"},
        ]
        return web.json_response(data)

    app = web.Application()
    app.router.add_get(
        "/apis/admin/v1/clusters/{cluster_name}/users", handle_list_cluster_user
    )

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/api/v1")) as client:
        quota = await client._admin.list_cluster_users()
        assert quota == [
            _ClusterUser(user_name="denis", role=_ClusterUserRoleType("admin")),
            _ClusterUser(user_name="andrew", role=_ClusterUserRoleType("manager")),
            _ClusterUser(user_name="ivan", role=_ClusterUserRoleType("user")),
        ]
