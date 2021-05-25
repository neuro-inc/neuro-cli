from decimal import Decimal
from typing import AsyncIterator, Callable

import pytest
from aiohttp import web
from yarl import URL

from neuro_sdk import Action, Client, Permission, ResourceNotFound
from neuro_sdk.users import Quota

from tests import _TestServerFactory

_MakeClient = Callable[..., Client]


@pytest.fixture()
async def mocked_share_client(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> AsyncIterator[Client]:
    async def handler(request: web.Request) -> web.Response:
        data = await request.json()
        assert data[0]["action"] in [item.value for item in Action]
        data[0]["action"] = Action.MANAGE.value
        return web.json_response(data, status=web.HTTPCreated.status_code)

    app = web.Application()
    app.router.add_post("/users/bill/permissions", handler)
    srv = await aiohttp_server(app)
    client = make_client(srv.make_url("/"))
    yield client
    await client.close()


@pytest.fixture()
async def mocked_revoke_client(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> AsyncIterator[Client]:
    async def handler(request: web.Request) -> web.Response:
        assert "uri" in request.query
        raise web.HTTPNoContent()

    app = web.Application()
    app.router.add_delete("/users/bill/permissions", handler)
    srv = await aiohttp_server(app)
    client = make_client(srv.make_url("/"))
    yield client
    await client.close()


@pytest.fixture()
async def mocked_add_role_client(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> AsyncIterator[Client]:
    async def handler(request: web.Request) -> web.Response:
        data = await request.json()
        assert data["name"].startswith("mycompany/")
        raise web.HTTPCreated()

    app = web.Application()
    app.router.add_post("/users", handler)
    srv = await aiohttp_server(app)
    client = make_client(srv.make_url("/"))
    yield client
    await client.close()


@pytest.fixture()
async def mocked_remove_role_client(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> AsyncIterator[Client]:
    async def handler(request: web.Request) -> web.Response:
        assert request.match_info["name"].startswith("mycompany:")
        raise web.HTTPNoContent()

    app = web.Application()
    app.router.add_delete("/users/{name}", handler)
    srv = await aiohttp_server(app)
    client = make_client(srv.make_url("/"))
    yield client
    await client.close()


@pytest.fixture()
async def mocked_get_user_client(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> AsyncIterator[Client]:
    async def handler(request: web.Request) -> web.Response:
        assert request.match_info["name"] == "test_user"
        return web.json_response(
            {
                "user_name": "test_user",
                "clusters": [
                    {"name": "cluster1"},
                    {"name": "cluster2", "quota": {}},
                    {"name": "cluster3", "quota": {"credits": "100"}},
                    {"name": "cluster4", "quota": {"total_running_jobs": 5}},
                    {
                        "name": "cluster5",
                        "quota": {"credits": "100", "total_running_jobs": 5},
                    },
                ],
            },
            status=web.HTTPOk.status_code,
        )

    app = web.Application()
    app.router.add_get("/users/{name}", handler)
    srv = await aiohttp_server(app)
    client = make_client(srv.make_url("/"))
    yield client
    await client.close()


class TestUsers:
    async def test_get_quota(self, mocked_get_user_client: Client) -> None:
        res = await mocked_get_user_client.users.get_quota(
            user="test_user",
        )
        assert res["cluster1"] == Quota()
        assert res["cluster2"] == Quota()
        assert res["cluster3"] == Quota(credits=Decimal("100"))
        assert res["cluster4"] == Quota(total_running_jobs=5)
        assert res["cluster5"] == Quota(credits=Decimal("100"), total_running_jobs=5)

    async def test_share_unknown_user(self, mocked_share_client: Client) -> None:
        with pytest.raises(ResourceNotFound):
            await mocked_share_client.users.share(
                user="not-exists",
                permission=Permission(URL("storage://bob/resource"), Action.READ),
            )

    async def test_share_invalid_name(self, mocked_share_client: Client) -> None:
        with pytest.raises(ValueError):
            await mocked_share_client.users.share(
                user="mycompany/team:role",
                permission=Permission(URL("storage://bob/resource"), Action.READ),
            )

    async def test_correct_share(self, mocked_share_client: Client) -> None:
        ret = await mocked_share_client.users.share(
            user="bill",
            permission=Permission(URL("storage://bob/resource"), Action.READ),
        )
        assert ret == Permission(URL("storage://bob/resource"), Action.MANAGE)

    async def test_revoke_unknown_user(self, mocked_revoke_client: Client) -> None:
        with pytest.raises(ResourceNotFound):
            await mocked_revoke_client.users.revoke(
                user="not-exists", uri=URL("storage://bob/resource")
            )

    async def test_revoke_invalid_name(self, mocked_revoke_client: Client) -> None:
        with pytest.raises(ValueError):
            await mocked_revoke_client.users.revoke(
                user="mycompany/team:role", uri=URL("storage://bob/resource")
            )

    async def test_correct_revoke(self, mocked_revoke_client: Client) -> None:
        ret = await mocked_revoke_client.users.revoke(
            user="bill", uri=URL("storage://bob/resource")
        )
        assert ret is None  # at this moment no result

    async def test_add_role(self, mocked_add_role_client: Client) -> None:
        ret = await mocked_add_role_client.users.add("mycompany/team/role")
        assert ret is None  # at this moment no result

    async def test_remove_role(self, mocked_remove_role_client: Client) -> None:
        ret = await mocked_remove_role_client.users.remove("mycompany/team/role")
        assert ret is None  # at this moment no result

    async def test_remove_role_invalid_name(
        self, mocked_remove_role_client: Client
    ) -> None:
        with pytest.raises(ValueError):
            await mocked_remove_role_client.users.remove("mycompany/team:role")
