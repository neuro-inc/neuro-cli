from pathlib import Path
from typing import Optional, Set
from uuid import uuid4 as uuid

import pytest
from yarl import URL

from neuromation.api import ConfigError, Factory
from neuromation.api.config import _AuthToken, _Config, _PyPIVersion
from neuromation.api.jobs import _Jobs
from neuromation.api.login import AuthNegotiator, _AuthConfig, _ServerConfig


@pytest.fixture
def token():
    return str(uuid())


@pytest.fixture
def tmp_home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)  # Like as it's not enough
    monkeypatch.setenv("HOME", str(tmp_path))

    return tmp_path


@pytest.fixture
def config_file(tmp_home, auth_config):
    config_path = tmp_home / ".nmrc"
    _create_config(config_path, auth_config)
    return config_path


def _create_config(nmrc_path: Path, auth_config):
    token = str(uuid())
    config = _Config(
        auth_config=auth_config,
        auth_token=_AuthToken.create_non_expiring(token),
        pypi=_PyPIVersion.create_uninitialized(),
        url=URL("https://dev.neu.ro/api/v1"),
        registry_url=URL("https://registry-dev.neu.ro"),
    )
    Factory(nmrc_path)._save(config)
    assert nmrc_path.exists()
    return token


async def test_get_method_with_empty_path(tmp_home, auth_config):
    token = _create_config(tmp_home / ".nmrc", auth_config)
    client = await Factory().get()
    await client.close()
    assert client._config.auth_token.token == token


async def test_get_method_with_shorten_path(tmp_home, auth_config):
    token = _create_config(tmp_home / "test.nmrc", auth_config)
    client = await Factory(Path("~/test.nmrc")).get()
    await client.close()
    assert client._config.auth_token.token == token


async def test_get_method_with_full_path(tmp_home, auth_config):
    config_path = tmp_home / "test.nmrc"
    token = _create_config(config_path, auth_config)
    client = await Factory(config_path).get()
    await client.close()
    assert client._config.auth_token.token == token


async def test_get_method_with_refreshed_token(config_file, monkeypatch):
    new_token = str(uuid()) + "changed" * 10  # token must has other size

    async def _refresh_token_mock(self, token):
        return _AuthToken.create_non_expiring(new_token)

    monkeypatch.setattr(AuthNegotiator, "refresh_token", _refresh_token_mock)
    file_stat_before = config_file.stat()
    client = await Factory().get()
    await client.close()
    file_stat_after = config_file.stat()
    assert client._config.auth_token.token == new_token
    assert (
        file_stat_before != file_stat_after
    ), "Config wile not rewritten while token refreshed"


async def test_login_already_logged(config_file):
    with pytest.raises(ConfigError, match=r"already exists"):
        await Factory().login()


async def test_normal_login(tmp_home, monkeypatch, aiohttp_server):

    new_token = str(uuid())

    async def _refresh_token_mock(
        self, token: Optional[_AuthToken] = None
    ) -> _AuthToken:
        return _AuthToken.create_non_expiring(new_token)

    async def _get_server_config_mock(url: URL) -> _ServerConfig:
        auth_config = _AuthConfig(
            auth_url=URL(),
            token_url=URL(),
            client_id="bobby",
            audience="https://test.dev",
            callback_urls=[URL("https://test.dev/cb")],
        )
        return _ServerConfig(
            auth_config=auth_config, registry_url=URL("https://registry.test.dev/")
        )

    async def _jobs_list_mock(
        self, statuses: Optional[Set[str]] = None, name: Optional[str] = None
    ):
        return []

    monkeypatch.setattr(AuthNegotiator, "refresh_token", _refresh_token_mock)
    monkeypatch.setattr(_Jobs, "list", _jobs_list_mock)
    monkeypatch.setattr(
        "neuromation.api.login.get_server_config", _jobs_list_mock
    )  # problem here
    await Factory().login()
