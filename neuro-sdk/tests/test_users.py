from typing import AsyncIterator, Callable

import pytest
from aiohttp import web
from yarl import URL

from neuro_sdk import Action, Client, Permission, ResourceNotFound

from tests import _TestServerFactory

_MakeClient = Callable[..., Client]


@pytest.fixture()
async def mocked_share_client(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> AsyncIterator[Client]:
    async def handler(request: web.Request) -> web.Response:
        data = await request.json()
        assert data[0]["action"] in [item.value for item in Action]
        raise web.HTTPCreated()

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


class TestUsersShare:
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
        assert ret is None  # at this moment no result

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
