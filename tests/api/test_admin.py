from typing import Callable

from aiohttp import web
from aiohttp.web import HTTPCreated, HTTPNoContent

from neuromation.api import Client
from neuromation.api.admin import _ClusterUser, _ClusterUserRoleType
from tests import _TestServerFactory


_MakeClient = Callable[..., Client]


async def test_list_cluster_users_explicit_cluster(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    requested_clusters = []

    async def handle_list_cluster_user(request: web.Request) -> web.StreamResponse:
        requested_clusters.append(request.match_info["cluster_name"])
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
        resp = await client._admin.list_cluster_users("my_cluster")
        assert resp == [
            _ClusterUser(user_name="denis", role=_ClusterUserRoleType("admin")),
            _ClusterUser(user_name="andrew", role=_ClusterUserRoleType("manager")),
            _ClusterUser(user_name="ivan", role=_ClusterUserRoleType("user")),
        ]
        assert requested_clusters == ["my_cluster"]


async def test_list_cluster_users_default_cluster(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    requested_clusters = []

    async def handle_list_cluster_user(request: web.Request) -> web.StreamResponse:
        requested_clusters.append(request.match_info["cluster_name"])
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
        resp = await client._admin.list_cluster_users()
        assert resp == [
            _ClusterUser(user_name="denis", role=_ClusterUserRoleType("admin")),
            _ClusterUser(user_name="andrew", role=_ClusterUserRoleType("manager")),
            _ClusterUser(user_name="ivan", role=_ClusterUserRoleType("user")),
        ]
        assert requested_clusters == ["default"]


async def test_add_cluster_user(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    requested_clusters = []
    requested_payloads = []

    async def handle_add_cluster_user(request: web.Request) -> web.StreamResponse:
        payload = await request.json()
        requested_clusters.append(request.match_info["cluster_name"])
        requested_payloads.append(payload)
        return web.json_response(payload, status=HTTPCreated.status_code)

    app = web.Application()
    app.router.add_post(
        "/apis/admin/v1/clusters/{cluster_name}/users", handle_add_cluster_user
    )

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/api/v1")) as client:
        resp = await client._admin.add_cluster_user("default", "ivan", "user")
        assert resp == _ClusterUser(user_name="ivan", role=_ClusterUserRoleType("user"))
        assert requested_clusters == ["default"]
        assert requested_payloads == [{"role": "user", "user_name": "ivan"}]


async def test_remove_cluster_user(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    requested_cluster_users = []

    async def handle_remove_cluster_user(request: web.Request) -> web.StreamResponse:
        requested_cluster_users.append(
            (request.match_info["cluster_name"], request.match_info["user_name"],)
        )
        return web.json_response(status=HTTPNoContent.status_code)

    app = web.Application()
    app.router.add_delete(
        "/apis/admin/v1/clusters/{cluster_name}/users/{user_name}",
        handle_remove_cluster_user,
    )

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/api/v1")) as client:
        await client._admin.remove_cluster_user("default", "ivan")
        assert requested_cluster_users == [("default", "ivan")]
