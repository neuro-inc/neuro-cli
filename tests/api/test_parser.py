from typing import Callable

import pytest

from neuromation.api import Client, LocalImage, RemoteImage


_MakeClient = Callable[..., Client]


@pytest.mark.parametrize(
    "volume", ["storage:///", ":", "::::", "", "storage:///data/:/data/rest:wrong"]
)
async def test_volume_from_str_fail(volume: str, make_client: _MakeClient) -> None:
    async with make_client("https://example.com") as client:
        with pytest.raises(ValueError):
            client.parse.volume(volume)


async def test_parse_local(make_client: _MakeClient) -> None:
    async with make_client("https://api.localhost.localdomain") as client:
        result = client.parse.local_image("bananas:latest")
    assert result == LocalImage("bananas", "latest")


async def test_parse_remote(make_client: _MakeClient) -> None:
    async with make_client("https://api.localhost.localdomain") as client:
        result = client.parse.remote_image("image://bob/bananas:latest")
    assert result == RemoteImage(
        "bananas", "latest", owner="bob", registry="registry-dev.neu.ro"
    )
