from typing import Callable

from neuromation.api import Client


_MakeClient = Callable[..., Client]


async def test_client_username(make_client: _MakeClient) -> None:
    async with make_client("http://example.com") as client:
        assert client.username == "user"
