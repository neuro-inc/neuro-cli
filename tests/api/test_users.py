from dataclasses import dataclass

import pytest
from aiohttp import web
from yarl import URL

from neuromation.api import Action, IllegalArgumentError, Permission, ResourceNotFound


@pytest.fixture()
async def mocked_share_client(aiohttp_server, make_client):
    async def handler(request):
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
async def mocked_revoke_client(aiohttp_server, make_client):
    async def handler(request):
        assert "uri" in request.query
        raise web.HTTPNoContent()

    app = web.Application()
    app.router.add_delete("/users/bill/permissions", handler)
    srv = await aiohttp_server(app)
    client = make_client(srv.make_url("/"))
    yield client
    await client.close()


class TestUsersShare:
    def test_permissions_from_cli(self):
        with pytest.raises(ValueError, match=r"URI Scheme not specified"):
            Permission.from_cli("bob", URL("scheme-less/resource"), Action.MANAGE)

        with pytest.raises(ValueError, match=r"Unsupported URI scheme"):
            Permission.from_cli("bob", URL("http://neuromation.io"), Action.READ)

        user_less_permission = Permission.from_cli(
            "bob", URL("storage:resource"), Action.MANAGE
        )
        full_permission = Permission.from_cli(
            "bob", URL("storage://bob/resource"), Action.MANAGE
        )
        assert user_less_permission == full_permission

    async def test_share_unknown_user(self, mocked_share_client):
        with pytest.raises(ResourceNotFound):
            await mocked_share_client.users.share(
                user="not-exists",
                permission=Permission(URL("storage://bob/resource"), Action.READ),
            )

    async def test_share_unsupported_action(self, mocked_share_client):
        @dataclass()
        class FunnyAction:
            value: str

        with pytest.raises(IllegalArgumentError):
            await mocked_share_client.users.share(
                user="bill",
                permission=Permission(
                    URL("storage://bob/resource"), FunnyAction("amuse")
                ),
            )

    async def test_correct_share(self, mocked_share_client):
        ret = await mocked_share_client.users.share(
            user="bill",
            permission=Permission(URL("storage://bob/resource"), Action.READ),
        )
        assert ret is None  # at this moment no result

    async def test_revoke_unknown_user(self, mocked_revoke_client):
        with pytest.raises(ResourceNotFound):
            await mocked_revoke_client.users.revoke(
                user="not-exists", uri=URL("storage://bob/resource")
            )

    async def test_correct_revoke(self, mocked_revoke_client):
        ret = await mocked_revoke_client.users.revoke(
            user="bill", uri=URL("storage://bob/resource")
        )
        assert ret is None  # at this moment no result
