from pathlib import Path
import sys

import pytest
from yarl import URL

from neuromation.client import Client
from neuromation.client.url_utils import (
    normalize_local_path_uri,
    normalize_storage_path_uri,
)


@pytest.fixture
async def client(loop, token):
    async with Client(URL("https://example.com"), token) as client:
        yield client


# asvetlov: I don't like autouse but it is the fastest fix
@pytest.fixture(autouse=True)
def fake_homedir(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    return Path.home()


@pytest.fixture
def pwd():
    return Path.cwd()


async def test_config_username(token, client):
    assert client.cfg.username == "user"


async def test_normalize_storage_path_uri__0_slashes_relative(token, client):
    url = URL("storage:path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/path/to/file.txt"
    assert str(url) == "storage://user/path/to/file.txt"


async def test_normalize_local_path_uri__0_slashes_relative(token, pwd):
    url = URL("file:path/to/file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert url.path == f"{pwd}/path/to/file.txt"
    assert str(url) == f"file://{pwd}/path/to/file.txt"


async def test_normalize_storage_path_uri__1_slash_absolute(token, client):
    url = URL("storage:/path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/path/to/file.txt"
    assert str(url) == "storage://user/path/to/file.txt"


async def test_normalize_local_path_uri__1_slash_absolute(token, pwd):
    url = URL("file:/path/to/file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert url.path == "/path/to/file.txt"
    assert str(url) == "file:///path/to/file.txt"


async def test_normalize_storage_path_uri__2_slashes(token, client):
    url = URL("storage://path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "path"
    assert url.path == "/to/file.txt"
    assert str(url) == "storage://path/to/file.txt"


async def test_normalize_local_path_uri__2_slashes(token, pwd):
    url = URL("file://path/to/file.txt")
    with pytest.raises(ValueError, match="Host part is not allowed, found 'path'"):
        url = normalize_local_path_uri(url)


async def test_normalize_storage_path_uri__3_slashes_relative(token, client):
    url = URL("storage:///path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/path/to/file.txt"
    assert str(url) == "storage://user/path/to/file.txt"


async def test_normalize_local_path_uri__3_slashes_relative(token, pwd):
    url = URL("file:///path/to/file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert url.path == "/path/to/file.txt"
    assert str(url) == "file:///path/to/file.txt"


async def test_normalize_storage_path_uri__4_slashes_relative(token, client):
    url = URL("storage:////path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/path/to/file.txt"
    assert str(url) == "storage://user/path/to/file.txt"


async def test_normalize_local_path_uri__4_slashes_relative(token, pwd):
    url = URL("file:////path/to/file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert url.path == "/path/to/file.txt"
    assert str(url) == "file:///path/to/file.txt"


async def test_normalize_storage_path_uri__tilde_in_relative_path(token, client):
    url = URL("storage:~/path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/~/path/to/file.txt"
    assert str(url) == "storage://user/~/path/to/file.txt"


async def test_normalize_local_path_uri__tilde_in_relative_path(token, fake_homedir):
    url = URL("file:~/path/to/file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert url.path == f"{fake_homedir}/path/to/file.txt"
    assert str(url) == f"file://{fake_homedir}/path/to/file.txt"


async def test_normalize_storage_path_uri__tilde_in_absolute_path(token, client):
    url = URL("storage:/~/path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/~/path/to/file.txt"
    assert str(url) == "storage://user/~/path/to/file.txt"


async def test_normalize_local_path_uri__tilde_in_absolute_path(token):
    url = URL("file:/~/path/to/file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert url.path == "/~/path/to/file.txt"
    assert str(url) == "file:///~/path/to/file.txt"


async def test_normalize_storage_path_uri__tilde_in_host(token, client):
    url = URL("storage://~/path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/path/to/file.txt"


async def test_normalize_local_path_uri__tilde_in_host(token, client, pwd):
    url = URL("file://~/path/to/file.txt")
    with pytest.raises(ValueError, match=f"Host part is not allowed, found '~'"):
        url = normalize_local_path_uri(url)


async def test_normalize_storage_path_uri__bad_scheme(token, client):
    with pytest.raises(ValueError, match="Invalid storage scheme 'other://'"):
        url = URL("other:path/to/file.txt")
        normalize_storage_path_uri(url, client.username)


async def test_normalize_local_path_uri__bad_scheme(token):
    with pytest.raises(ValueError, match="Invalid local file scheme 'other://'"):
        url = URL("other:path/to/file.txt")
        normalize_local_path_uri(url)


# The tests below check that f(f(x)) == f(x) where f is a path normalization function


async def test_normalize_storage_path_uri__no_slash__double(token, client):
    url = URL("storage:path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/path/to/file.txt"
    assert str(url) == "storage://user/path/to/file.txt"


async def test_normalize_local_path_uri__no_slash__double(token, pwd):
    url = URL("file:path/to/file.txt")
    url = normalize_local_path_uri(url)
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert url.path == f"{pwd}/path/to/file.txt"
    assert str(url) == f"file://{pwd}/path/to/file.txt"


async def test_normalize_storage_path_uri__tilde_slash__double(token, client):
    url = URL("storage:~/path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/~/path/to/file.txt"
    assert str(url) == "storage://user/~/path/to/file.txt"


async def test_normalize_local_path_uri__tilde_slash__double(token, fake_homedir):
    url = URL("file:~/path/to/file.txt")
    url = normalize_local_path_uri(url)
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert url.path == f"{fake_homedir}/path/to/file.txt"
    assert str(url) == f"file://{fake_homedir}/path/to/file.txt"


async def test_normalize_storage_path_uri__3_slashes__double(token, client):
    url = URL("storage:///path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/path/to/file.txt"
    assert str(url) == "storage://user/path/to/file.txt"


async def test_normalize_local_path_uri__3_slashes__double(token, fake_homedir):
    url = URL("file:///path/to/file.txt")
    url = normalize_local_path_uri(url)
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert url.path == "/path/to/file.txt"
    assert str(url) == "file:///path/to/file.txt"


@pytest.mark.skipif(sys.platform != 'win32', reason='Requires Windows')
def test_normalized_path():
    p = URL('file:///Z:/neuromation/platform-api-clients/python/setup.py')
    assert normalize_local_path_uri(p) == p
