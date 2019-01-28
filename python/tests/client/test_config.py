import pytest
from yarl import URL

from neuromation.client import Client


async def test_username(token):
    async with Client("https://example.com", token) as client:
        assert client.cfg.username == "user"


async def test_storage_normalize(token):
    async with Client("https://example.com", token) as client:
        url = client.cfg.norm_storage(URL("storage:path/to/file.txt"))
        assert url.scheme == "storage"
        assert url.host == "user"
        assert url.path == "/path/to/file.txt"


async def test_storage_normalize_home_dir(token):
    async with Client("https://example.com", token) as client:
        url = client.cfg.norm_storage(URL("storage://~/file.txt"))
        assert url.scheme == "storage"
        assert url.host == "user"
        assert url.path == "/file.txt"


async def test_storage_normalize_bad_scheme(token):
    async with Client("https://example.com", token) as client:
        with pytest.raises(
            ValueError, match="Path should be targeting platform storage."
        ):
            client.cfg.norm_storage(URL("other:path/to/file.txt"))


@pytest.mark.xfail
async def test_storage_normalize_local(token):
    async with Client("https://example.com", token) as client:
        url = client.cfg.norma_file(URL("file:///path/to/file.txt"))
        assert url.scheme == "file"
        assert url.host is None
        # fails on CI only :(
        assert url.path == "/path/to/file.txt"


async def test_storage_normalize_local_bad_scheme(token):
    async with Client("https://example.com", token) as client:
        with pytest.raises(
            ValueError, match="Path should be targeting local file system."
        ):
            client.cfg.norm_file(URL("other:path/to/file.txt"))


@pytest.mark.xfail
async def test_storage_normalize_local_expand_user(token, monkeypatch):
    monkeypatch.setenv("HOME", "/home/user")
    async with Client("https://example.com", token) as client:
        url = client.cfg.norm_file(URL("file:~/path/to/file.txt"))
        assert url.scheme == "file"
        assert url.host is None
        # fails on CI only :(
        assert url.path == "/home/user/path/to/file.txt"


async def test_storage_normalize_local_with_host(token):
    async with Client("https://example.com", token) as client:
        with pytest.raises(ValueError, match="Host part is not allowed"):
            client.cfg.norm_file(URL("file://host/path/to/file.txt"))
