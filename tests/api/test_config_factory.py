import sys
from pathlib import Path
from typing import Any, List, Optional, Set
from uuid import uuid4 as uuid

import aiohttp
import pytest
import yaml
from aiohttp import web
from yarl import URL

import neuromation.api.config_factory
from neuromation.api import ConfigError, Factory
from neuromation.api.config import _AuthConfig, _AuthToken, _Config, _PyPIVersion
from neuromation.api.jobs import Jobs
from neuromation.api.login import AuthNegotiator, _ClusterConfig
from tests import _TestServerFactory


@pytest.fixture
def token() -> str:
    return str(uuid())


@pytest.fixture
def tmp_home(tmp_path: Path, monkeypatch: Any) -> Path:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)  # Like as it's not enough
    monkeypatch.setenv("HOME", str(tmp_path))

    return tmp_path


@pytest.fixture
def config_file(
    tmp_home: Path, auth_config: _AuthConfig, cluster_config: _ClusterConfig
) -> Path:
    config_path = tmp_home / ".nmrc"
    _create_config(config_path, auth_config, cluster_config)
    return config_path


@pytest.fixture
async def mock_for_login(monkeypatch: Any, aiohttp_server: _TestServerFactory) -> URL:
    async def _refresh_token_mock(
        self: Any, token: Optional[_AuthToken] = None
    ) -> _AuthToken:
        return _AuthToken.create_non_expiring(str(uuid()))

    async def _jobs_list_mock(
        self: Any, statuses: Optional[Set[str]] = None, name: Optional[str] = None
    ) -> List[str]:
        return []

    async def _config_handler(request: web.Request) -> web.Response:
        config_json = {
            "auth_url": "https://test-neuromation.auth0.com/authorize",
            "token_url": "https://test-neuromation.auth0.com/oauth/token",
            "client_id": "banana",
            "audience": "https://test.dev.neuromation.io",
            "headless_callback_url": "https://https://dev.neu.ro/oauth/show-code",
            "callback_urls": [
                "http://127.0.0.2:54540",
                "http://127.0.0.2:54541",
                "http://127.0.0.2:54542",
            ],
            "success_redirect_url": "https://neu.ro/#test",
        }

        if "Authorization" in request.headers:
            config_json.update(
                {
                    "registry_url": "https://registry-dev.test.com",
                    "storage_url": "https://storage-dev.test.com",
                    "users_url": "https://users-dev.test.com",
                    "monitoring_url": "https://monitoring-dev.test.com",
                }
            )
        return web.json_response(config_json)

    app = web.Application()
    app.router.add_get("/config", _config_handler)
    srv = await aiohttp_server(app)

    monkeypatch.setattr(AuthNegotiator, "refresh_token", _refresh_token_mock)
    monkeypatch.setattr(Jobs, "list", _jobs_list_mock)

    return srv.make_url("/")


def _create_config(
    nmrc_path: Path, auth_config: _AuthConfig, cluster_config: _ClusterConfig
) -> str:
    token = str(uuid())
    config = _Config(
        auth_config=auth_config,
        auth_token=_AuthToken.create_non_expiring(token),
        cluster_config=cluster_config,
        pypi=_PyPIVersion.create_uninitialized(),
        url=URL("https://dev.neu.ro/api/v1"),
    )
    Factory(nmrc_path)._save(config)
    assert nmrc_path.exists()
    return token


class TestConfig:
    def test_check_initialized(self) -> None:
        auth_config_good = _AuthConfig.create(
            auth_url=URL("auth_url"),
            token_url=URL("http://token"),
            client_id="client-id",
            audience="everyone",
            headless_callback_url=URL("https://https://dev.neu.ro/oauth/show-code"),
        )
        assert auth_config_good.is_initialized()

        cluster_config_good = _ClusterConfig.create(
            registry_url=URL("http://value"),
            storage_url=URL("http://value"),
            users_url=URL("http://value"),
            monitoring_url=URL("http://value"),
        )
        assert cluster_config_good.is_initialized()

        config = _Config(
            auth_config=auth_config_good,
            auth_token=_AuthToken(
                token="token", expiration_time=10, refresh_token="ok"
            ),
            cluster_config=cluster_config_good,
            pypi=_PyPIVersion(pypi_version="1.2.3", check_timestamp=20),
            url=URL("https://dev.neu.ro"),
        )
        config.check_initialized()  # check no exceptions

    def test_check_initialized_bad_auth_config(self) -> None:
        auth_config_bad = _AuthConfig.create(
            auth_url=URL(),  # empty
            token_url=URL("http://token"),
            client_id="client-id",
            audience="everyone",
            headless_callback_url=URL("https://https://dev.neu.ro/oauth/show-code"),
        )
        assert not auth_config_bad.is_initialized()

        cluster_config_good = _ClusterConfig.create(
            registry_url=URL("http://value"),
            storage_url=URL("http://value"),
            users_url=URL("http://value"),
            monitoring_url=URL("http://value"),
        )
        assert cluster_config_good.is_initialized()

        config = _Config(
            auth_config=auth_config_bad,
            auth_token=_AuthToken(
                token="token", expiration_time=10, refresh_token="ok"
            ),
            cluster_config=cluster_config_good,
            pypi=_PyPIVersion(pypi_version="1.2.3", check_timestamp=20),
            url=URL("https://dev.neu.ro"),
        )
        with pytest.raises(ValueError, match="Missing server configuration"):
            config.check_initialized()

    def test_check_initialized_bad_cluster_config(self) -> None:
        auth_config_bad = _AuthConfig.create(
            auth_url=URL("auth_url"),
            token_url=URL("http://token"),
            client_id="client-id",
            audience="everyone",
            headless_callback_url=URL("https://https://dev.neu.ro/oauth/show-code"),
        )
        assert auth_config_bad.is_initialized()

        cluster_config_good = _ClusterConfig.create(
            registry_url=URL(),  # empty
            storage_url=URL("http://value"),
            users_url=URL("http://value"),
            monitoring_url=URL("http://value"),
        )
        assert not cluster_config_good.is_initialized()

        config = _Config(
            auth_config=auth_config_bad,
            auth_token=_AuthToken(
                token="token", expiration_time=10, refresh_token="ok"
            ),
            cluster_config=cluster_config_good,
            pypi=_PyPIVersion(pypi_version="1.2.3", check_timestamp=20),
            url=URL("https://dev.neu.ro"),
        )
        with pytest.raises(ValueError, match="Missing server configuration"):
            config.check_initialized()


class TestConfigFileInteraction:
    async def test_config_file_absent(self, tmp_home: Path) -> None:
        with pytest.raises(ConfigError, match=r"file.+not exists"):
            await Factory().get()

    async def test_config_file_is_dir(self, tmp_home: Path) -> None:
        Path(tmp_home / ".nmrc").mkdir()
        with pytest.raises(ConfigError, match=r"not a regular file"):
            await Factory().get()

    async def test_default_path(
        self, tmp_home: Path, auth_config: _AuthConfig, cluster_config: _ClusterConfig
    ) -> None:
        token = _create_config(tmp_home / ".nmrc", auth_config, cluster_config)
        client = await Factory().get()
        await client.close()
        assert client._config.auth_token.token == token

    async def test_shorten_path(
        self, tmp_home: Path, auth_config: _AuthConfig, cluster_config: _ClusterConfig
    ) -> None:
        token = _create_config(tmp_home / "test.nmrc", auth_config, cluster_config)
        client = await Factory(Path("~/test.nmrc")).get()
        await client.close()
        assert client._config.auth_token.token == token

    async def test_full_path(
        self, tmp_home: Path, auth_config: _AuthConfig, cluster_config: _ClusterConfig
    ) -> None:
        config_path = tmp_home / "test.nmrc"
        token = _create_config(config_path, auth_config, cluster_config)
        client = await Factory(config_path).get()
        await client.close()
        assert client._config.auth_token.token == token

    async def test_token_autorefreshing(
        self, config_file: Path, monkeypatch: Any
    ) -> None:
        new_token = str(uuid()) + "changed" * 10  # token must has other size

        async def _refresh_token_mock(
            configf: _AuthConfig, token: _AuthToken, timeout: aiohttp.ClientTimeout
        ) -> _AuthToken:
            return _AuthToken.create_non_expiring(new_token)

        monkeypatch.setattr(
            neuromation.api.config_factory, "refresh_token", _refresh_token_mock
        )
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
    async def test_file_permissions(self, config_file: Path) -> None:
        Path(config_file).chmod(0o777)
        with pytest.raises(ConfigError, match=r"permission"):
            await Factory().get()

    async def test_mailformed_config(self, config_file: Path) -> None:
        # await Factory().login(url=mock_for_login)
        # config_file = tmp_home / ".nmrc"
        with config_file.open("r") as f:
            original = yaml.safe_load(f)

        for key in ["auth_config", "auth_token", "pypi", "cluster_config", "url"]:
            modified = original.copy()
            del modified[key]
            with config_file.open("w") as f:
                yaml.safe_dump(modified, f, default_flow_style=False)
            with pytest.raises(ConfigError, match=r"Malformed"):
                await Factory().get()


class TestLogin:
    async def test_login_already_logged(self, config_file: Path) -> None:
        with pytest.raises(ConfigError, match=r"already exists"):
            await Factory().login()

    async def test_normal_login(self, tmp_home: Path, mock_for_login: URL) -> None:
        await Factory().login(url=mock_for_login)
        nmrc_path = tmp_home / ".nmrc"
        assert Path(nmrc_path).exists(), "Config file not written after login "
        saved_config = Factory(nmrc_path)._read()
        assert saved_config.auth_config.is_initialized()
        assert saved_config.cluster_config.is_initialized()


class TestLoginWithToken:
    async def test_login_with_token_already_logged(self, config_file: Path) -> None:
        with pytest.raises(ConfigError, match=r"already exists"):
            await Factory().login_with_token(token="tokenstr")

    async def test_normal_login(self, tmp_home: Path, mock_for_login: URL) -> None:
        await Factory().login_with_token(token="tokenstr", url=mock_for_login)
        nmrc_path = tmp_home / ".nmrc"
        assert Path(nmrc_path).exists(), "Config file not written after login "
        saved_config = Factory(nmrc_path)._read()
        assert saved_config.auth_config.is_initialized()
        assert saved_config.cluster_config.is_initialized()


class TestLogout:
    async def test_logout(self, config_file: Path) -> None:
        await Factory().logout()
        assert not config_file.exists(), "Config not removed after logout"
