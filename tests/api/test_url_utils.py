import asyncio
import sys
from pathlib import Path
from typing import Any, AsyncIterator, Callable

import pytest
from yarl import URL

from neuromation.api import Client
from neuromation.api.url_utils import (
    _extract_path,
    normalize_local_path_uri,
    normalize_storage_path_uri,
    uri_from_cli,
)


@pytest.fixture
async def client(
    loop: asyncio.AbstractEventLoop, make_client: Callable[..., Client]
) -> AsyncIterator[Client]:
    async with make_client("https://example.com") as client:
        yield client


# asvetlov: I don't like autouse but it is the fastest fix
@pytest.fixture(autouse=True)
def fake_homedir(monkeypatch: Any, tmp_path: Path) -> Path:
    monkeypatch.setenv("HOME", str(tmp_path))
    return Path.home()


@pytest.fixture
def pwd() -> Path:
    return Path.cwd()


async def test_config_username(token: str, client: Client) -> None:
    assert client.username == "user"


def test_uri_from_cli_relative_path() -> None:
    uri = uri_from_cli("path/to/file.txt", "testuser")
    assert str(uri) == Path("path/to/file.txt").absolute().as_uri()


def test_uri_from_cli_absolute_path() -> None:
    uri = uri_from_cli("/path/to/file.txt", "testuser")
    assert str(uri) == Path("/path/to/file.txt").absolute().as_uri()


def test_uri_from_cli_relative_file_uri() -> None:
    uri = uri_from_cli("file:path/to/file.txt", "testuser")
    assert str(uri) == Path("path/to/file.txt").absolute().as_uri()


def test_uri_from_cli_absolute_file_uri() -> None:
    uri = uri_from_cli("file:/path/to/file.txt", "testuser")
    assert str(uri) == Path("/path/to/file.txt").absolute().as_uri()
    uri = uri_from_cli("file:///path/to/file.txt", "testuser")
    assert str(uri) == Path("/path/to/file.txt").absolute().as_uri()


def test_uri_from_cli_relative_storage_uri() -> None:
    uri = uri_from_cli("storage:path/to/file.txt", "testuser")
    assert str(uri) == "storage://testuser/path/to/file.txt"
    uri = uri_from_cli("storage:/path/to/file.txt", "testuser")
    assert str(uri) == "storage://path/to/file.txt"


def test_uri_from_cli_absolute_storage_uri() -> None:
    uri = uri_from_cli("storage://otheruser/path/to/file.txt", "testuser")
    assert str(uri) == "storage://otheruser/path/to/file.txt"
    uri = uri_from_cli("storage:///path/to/file.txt", "testuser")
    assert str(uri) == "storage://path/to/file.txt"


def test_uri_from_cli_numberic_path() -> None:
    uri = uri_from_cli("256", "testuser")
    assert str(uri) == Path("256").absolute().as_uri()
    uri = uri_from_cli("123456", "testuser")
    assert str(uri) == Path("123456").absolute().as_uri()
    uri = uri_from_cli("file:256", "testuser")
    assert str(uri) == Path("256").absolute().as_uri()
    uri = uri_from_cli("file:123456", "testuser")
    assert str(uri) == Path("123456").absolute().as_uri()
    uri = uri_from_cli("storage:256", "testuser")
    assert str(uri) == "storage://testuser/256"
    uri = uri_from_cli("storage:123456", "testuser")
    assert str(uri) == "storage://testuser/123456"


async def test_normalize_storage_path_uri_no_path(client: Client) -> None:
    url = URL("storage:")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/"
    assert str(url) == "storage://user"


async def test_normalize_local_path_uri_no_path(pwd: Path) -> None:
    url = URL("file:")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert _extract_path(url) == pwd


async def test_normalize_storage_path_uri_no_slashes(client: Client) -> None:
    url = URL("storage:file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/file.txt"
    assert str(url) == "storage://user/file.txt"


async def test_normalize_local_path_uri_no_slashes(pwd: Path) -> None:
    url = URL("file:file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert _extract_path(url) == pwd / "file.txt"


async def test_normalize_storage_path_uri__0_slashes_relative(client: Client) -> None:
    url = URL("storage:path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/path/to/file.txt"
    assert str(url) == "storage://user/path/to/file.txt"


async def test_normalize_local_path_uri__0_slashes_relative(pwd: Path) -> None:
    url = URL("file:path/to/file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert _extract_path(url) == pwd / "path/to/file.txt"


async def test_normalize_storage_path_uri__1_slash_absolute(client: Client) -> None:
    url = URL("storage:/path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "path"
    assert url.path == "/to/file.txt"
    assert str(url) == "storage://path/to/file.txt"


async def test_normalize_local_path_uri__1_slash_absolute(pwd: Path) -> None:
    url = URL("file:/path/to/file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert _extract_path(url) == Path(pwd.drive + "/path/to/file.txt")


async def test_normalize_storage_path_uri__2_slashes(client: Client) -> None:
    url = URL("storage://path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "path"
    assert url.path == "/to/file.txt"
    assert str(url) == "storage://path/to/file.txt"


async def test_normalize_local_path_uri__2_slashes(pwd: Path) -> None:
    url = URL("file://path/to/file.txt")
    with pytest.raises(ValueError, match="Host part is not allowed, found 'path'"):
        url = normalize_local_path_uri(url)


async def test_normalize_storage_path_uri__3_slashes_relative(client: Client) -> None:
    url = URL("storage:///path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "path"
    assert url.path == "/to/file.txt"
    assert str(url) == "storage://path/to/file.txt"


async def test_normalize_local_path_uri__3_slashes_relative(pwd: Path) -> None:
    url = URL("file:///path/to/file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert _extract_path(url) == Path(pwd.drive + "/path/to/file.txt")


async def test_normalize_storage_path_uri__4_slashes_relative(client: Client) -> None:
    url = URL("storage:////path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "path"
    assert url.path == "/to/file.txt"
    assert str(url) == "storage://path/to/file.txt"


@pytest.mark.skipif(sys.platform == "win32", reason="Doesn't work on Windows")
async def test_normalize_local_path_uri__4_slashes_relative() -> None:
    url = URL("file:////path/to/file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert url.path == "/path/to/file.txt"
    assert str(url) == f"file:///path/to/file.txt"


async def test_normalize_storage_path_uri__tilde_in_relative_path(
    client: Client,
) -> None:
    url = URL("storage:~/path/to/file.txt")
    with pytest.raises(ValueError, match=".*Cannot expand user.*"):
        normalize_storage_path_uri(url, client.username)


async def test_normalize_local_path_uri__tilde_in_relative_path(
    fake_homedir: Path,
) -> None:
    url = URL("file:~/path/to/file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert _extract_path(url) == fake_homedir / "path/to/file.txt"
    assert str(url) == (fake_homedir / "path/to/file.txt").as_uri()


async def test_normalize_storage_path_uri__tilde_in_relative_path_2(
    client: Client,
) -> None:
    url = URL("storage:./~/path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/~/path/to/file.txt"
    assert str(url) == "storage://user/~/path/to/file.txt"


async def test_normalize_local_path_uri__tilde_in_relative_path_2(
    fake_homedir: Path,
) -> None:
    url = URL("file:./~/path/to/file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert _extract_path(url) == fake_homedir / "path/to/file.txt"
    assert str(url) == (fake_homedir / "path/to/file.txt").as_uri()


async def test_normalize_storage_path_uri__tilde_in_relative_path_3(
    client: Client,
) -> None:
    url = URL("storage:path/to~file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/path/to~file.txt"
    assert str(url) == "storage://user/path/to~file.txt"


async def test_normalize_local_path_uri__tilde_in_relative_path_3(
    fake_homedir: Path, pwd: Path
) -> None:
    url = URL("file:path/to~file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert _extract_path(url) == pwd / "path/to~file.txt"
    assert str(url) == (pwd / "path/to~file.txt").as_uri().replace("%7E", "~")


async def test_normalize_storage_path_uri__tilde_in_absolute_path(
    client: Client,
) -> None:
    url = URL("storage:/~/path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/path/to/file.txt"
    assert str(url) == "storage://user/path/to/file.txt"


async def test_normalize_local_path_uri__tilde_in_absolute_path(
    fake_homedir: Path, pwd: Path
) -> None:
    url = URL("file:/~/path/to/file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert _extract_path(url) == pwd / "/~/path/to/file.txt"
    assert str(url) == (pwd / "/~/path/to/file.txt").as_uri().replace("%7E", "~")


async def test_normalize_storage_path_uri__tilde_in_host(client: Client) -> None:
    url = URL("storage://~/path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/path/to/file.txt"


async def test_normalize_local_path_uri__tilde_in_host(
    client: Client, pwd: Path
) -> None:
    url = URL("file://~/path/to/file.txt")
    with pytest.raises(ValueError, match=f"Host part is not allowed, found '~'"):
        url = normalize_local_path_uri(url)


async def test_normalize_storage_path_uri__bad_scheme(client: Client) -> None:
    with pytest.raises(ValueError, match="Invalid storage scheme 'other://'"):
        url = URL("other:path/to/file.txt")
        normalize_storage_path_uri(url, client.username)


async def test_normalize_local_path_uri__bad_scheme() -> None:
    with pytest.raises(ValueError, match="Invalid local file scheme 'other://'"):
        url = URL("other:path/to/file.txt")
        normalize_local_path_uri(url)


# The tests below check that f(f(x)) == f(x) where f is a path normalization function


async def test_normalize_storage_path_uri__no_slash__double(client: Client) -> None:
    url = URL("storage:path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "user"
    assert url.path == "/path/to/file.txt"
    assert str(url) == "storage://user/path/to/file.txt"


async def test_normalize_local_path_uri__no_slash__double(pwd: Path) -> None:
    url = URL("file:path/to/file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert _extract_path(url) == pwd / "path/to/file.txt"


async def test_normalize_storage_path_uri__tilde_slash__double(client: Client) -> None:
    url = URL("storage:~/path/to/file.txt")
    with pytest.raises(ValueError, match=".*Cannot expand user.*"):
        normalize_storage_path_uri(url, client.username)


async def test_normalize_local_path_uri__tilde_slash__double(
    fake_homedir: Path,
) -> None:
    url = URL("file:~/path/to/file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert _extract_path(url) == fake_homedir / "path/to/file.txt"
    assert str(url) == (fake_homedir / "path/to/file.txt").as_uri()


async def test_normalize_storage_path_uri__3_slashes__double(client: Client) -> None:
    url = URL("storage:///path/to/file.txt")
    url = normalize_storage_path_uri(url, client.username)
    assert url.scheme == "storage"
    assert url.host == "path"
    assert url.path == "/to/file.txt"
    assert str(url) == "storage://path/to/file.txt"


async def test_normalize_local_path_uri__3_slashes__double(pwd: Path) -> None:
    url = URL(f"file:///{pwd}/path/to/file.txt")
    url = normalize_local_path_uri(url)
    assert url.scheme == "file"
    assert url.host is None
    assert _extract_path(url) == pwd / "path/to/file.txt"
    assert str(url) == (pwd / "path/to/file.txt").as_uri()


@pytest.mark.skipif(sys.platform != "win32", reason="Requires Windows")
def test_normalized_path() -> None:
    p = URL("file:///Z:/neuromation/platform-api-clients/python/setup.py")
    assert normalize_local_path_uri(p) == p
