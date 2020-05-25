from typing import Callable

import pytest
from yarl import URL

from neuromation.api import Client, LocalImage, RemoteImage
from neuromation.api.parsing_utils import _get_url_authority


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
        result = client.parse.remote_image("image://test-cluster/bob/bananas:latest")
    assert result == RemoteImage.new_neuro_image(
        name="bananas",
        tag="latest",
        owner="bob",
        registry="registry-dev.neu.ro",
        cluster_name="test-cluster",
    )


async def test_parse_remote_registry_image(make_client: _MakeClient) -> None:
    async with make_client(
        "https://api.localhost.localdomain", registry_url="http://localhost:5000"
    ) as client:
        result = client.parse.remote_image("localhost:5000/bob/library/bananas:latest")
    assert result == RemoteImage.new_neuro_image(
        name="library/bananas",
        tag="latest",
        owner="bob",
        registry="localhost:5000",
        cluster_name="default",
    )


async def test_parse_remote_public(make_client: _MakeClient) -> None:
    async with make_client(
        "https://api.localhost.localdomain", registry_url="http://localhost:5000"
    ) as client:
        result = client.parse.remote_image("ubuntu:latest")
    assert result == RemoteImage.new_external_image(name="ubuntu", tag="latest")


def test_get_url_authority_with_explicit_port() -> None:
    url = URL("http://example.com:8080/")
    assert _get_url_authority(url) == "example.com:8080"


def test_get_url_authority_with_implicit_port() -> None:
    url = URL("http://example.com/")  # here `url.port == 80`
    assert _get_url_authority(url) == "example.com"


def test_get_url_authority_without_port() -> None:
    url = URL("scheme://example.com/")  # here `url.port is None`
    assert _get_url_authority(url) == "example.com"


def test_get_url_authority_without_host() -> None:
    url = URL("scheme://")
    assert _get_url_authority(url) is None
