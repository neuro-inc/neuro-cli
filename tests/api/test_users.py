from typing import AsyncIterator, Callable

import pytest
from aiohttp import web
from yarl import URL

from neuromation.api import Action, Client, Permission, ResourceNotFound
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


class TestUsersShare:
    async def test_share_unknown_user(self, mocked_share_client: Client) -> None:
        with pytest.raises(ResourceNotFound):
            await mocked_share_client.users.share(
                user="not-exists",
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

    async def test_correct_revoke(self, mocked_revoke_client: Client) -> None:
        ret = await mocked_revoke_client.users.revoke(
            user="bill", uri=URL("storage://bob/resource")
        )
        assert ret is None  # at this moment no result
