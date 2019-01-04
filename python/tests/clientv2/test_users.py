from dataclasses import dataclass

import pytest
from aiohttp import web
from yarl import URL

from neuromation.client.client import IllegalArgumentError, ResourceNotFound
from neuromation.clientv2 import Action, ClientV2, Permission, User


@pytest.fixture()
async def mocked_share_client(aiohttp_server):
    async def handler(request):
        data = await request.json()
        assert data[0]["action"] in [item.value for item in Action]
        return web.HTTPCreated()

    app = web.Application()
    app.router.add_post("/users/bill/permissions", handler)
    srv = await aiohttp_server(app)
    client = ClientV2(srv.make_url("/"), "token")
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
                user=User(name="not-exists"),
                permission=Permission(URL("storage://bob/resource"), Action.READ),
            )

    async def test_share_unsupported_action(self, mocked_share_client):
        @dataclass()
        class FunnyAction:
            value: str

        with pytest.raises(IllegalArgumentError):
            await mocked_share_client.users.share(
                user=User(name="bill"),
                permission=Permission(
                    URL("storage://bob/resource"), FunnyAction("amuse")
                ),
            )

    async def test_correct_share(self, mocked_share_client):
        ret = await mocked_share_client.users.share(
            user=User(name="bill"),
            permission=Permission(URL("storage://bob/resource"), Action.READ),
        )
        assert ret is None  # at this moment no result
