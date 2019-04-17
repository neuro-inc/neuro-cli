import sys
from pathlib import Path
from typing import Optional, Set
from uuid import uuid4 as uuid

import pytest
import yaml
from aiohttp import web
from yarl import URL

from neuromation.api import ConfigError, Factory
from neuromation.api.config import _AuthToken, _Config, _PyPIVersion
from neuromation.api.jobs import _Jobs
from neuromation.api.login import AuthNegotiator


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


@pytest.fixture
async def mock_for_login(monkeypatch, aiohttp_server):
    async def _refresh_token_mock(
        self, token: Optional[_AuthToken] = None
    ) -> _AuthToken:
        return _AuthToken.create_non_expiring(str(uuid()))

    async def _jobs_list_mock(
        self, statuses: Optional[Set[str]] = None, name: Optional[str] = None
    ):
        return []

    async def _config_handler(request):
        return web.json_response(
            {
                "registry_url": "https://registry-dev.test.com",
                "auth_url": "https://test-neuromation.auth0.com/authorize",
                "token_url": "https://test-neuromation.auth0.com/oauth/token",
                "client_id": "banana",
                "audience": "https://test.dev.neuromation.io",
                "callback_urls": [
                    "http://127.0.0.2:54540",
                    "http://127.0.0.2:54541",
                    "http://127.0.0.2:54542",
                ],
                "success_redirect_url": "https://neu.ro/#test",
            }
        )

    app = web.Application()
    app.router.add_get("/config", _config_handler)
    srv = await aiohttp_server(app)

    monkeypatch.setattr(AuthNegotiator, "refresh_token", _refresh_token_mock)
    monkeypatch.setattr(_Jobs, "list", _jobs_list_mock)

    return srv.make_url("/")


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


class TestConfigFileInteraction:
    async def test_config_file_absent(self, tmp_home):
        with pytest.raises(ConfigError, match=r"file.+not exists"):
            await Factory().get()

    async def test_config_file_is_dir(self, tmp_home):
        Path(tmp_home / ".nmrc").mkdir()
        with pytest.raises(ConfigError, match=r"not a regular file"):
            await Factory().get()

    async def test_default_path(self, tmp_home, auth_config):
        token = _create_config(tmp_home / ".nmrc", auth_config)
        client = await Factory().get()
        await client.close()
        assert client._config.auth_token.token == token

    async def test_shorten_path(self, tmp_home, auth_config):
        token = _create_config(tmp_home / "test.nmrc", auth_config)
        client = await Factory(Path("~/test.nmrc")).get()
        await client.close()
        assert client._config.auth_token.token == token

    async def test_full_path(self, tmp_home, auth_config):
        config_path = tmp_home / "test.nmrc"
        token = _create_config(config_path, auth_config)
        client = await Factory(config_path).get()
        await client.close()
        assert client._config.auth_token.token == token

    async def test_token_autorefreshing(self, config_file, monkeypatch):
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
        ), "Config file not rewritten while token refreshed"

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Windows does not supports UNIX-like permissions",
    )
    async def test_file_permissions(self, config_file):
        Path(config_file).chmod(0o777)
        with pytest.raises(ConfigError, match=r"permission"):
            await Factory().get()

    async def test_mailformed_config(self, config_file):
        # await Factory().login(url=mock_for_login)
        # config_file = tmp_home / ".nmrc"
        with config_file.open("r") as f:
            original = yaml.safe_load(f)

        for key in ["auth_config", "auth_token", "pypi", "registry_url", "url"]:
            modified = original.copy()
            del modified[key]
            with config_file.open("w") as f:
                yaml.safe_dump(modified, f, default_flow_style=False)
            with pytest.raises(ConfigError, match=r"Malformed"):
                await Factory().get()


class TestLogin:
    async def test_login_already_logged(self, config_file):
        with pytest.raises(ConfigError, match=r"already exists"):
            await Factory().login()

    async def test_normal_login(self, tmp_home, mock_for_login):
        await Factory().login(url=mock_for_login)
        assert Path(tmp_home / ".nmrc").exists(), "Config file not written after login "


class TestLoginWithToken:
    async def test_login_with_token_already_logged(self, config_file):
        with pytest.raises(ConfigError, match=r"already exists"):
            await Factory().login_with_token(token="tokenstr")

    async def test_normal_login(self, tmp_home, mock_for_login):
        await Factory().login_with_token(token="tokenstr", url=mock_for_login)
        assert Path(tmp_home / ".nmrc").exists(), "Config file not written after login "


class TestLogout:
    async def test_logout(self, config_file):
        await Factory().logout()
        assert not config_file.exists(), "Config not removed after logout"
