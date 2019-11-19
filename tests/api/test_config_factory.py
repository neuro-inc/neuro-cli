import sys
from pathlib import Path
from typing import Any, Dict
from unittest import mock

import aiohttp
import pytest
import yaml
from aiohttp import web
from aiohttp.test_utils import TestServer as _TestServer
from jose import jwt
from yarl import URL

import neuromation
import neuromation.api.config_factory
from neuromation.api import TRUSTED_CONFIG_PATH, ConfigError, Factory
from neuromation.api.config import (
    _AuthConfig,
    _AuthToken,
    _Config,
    _CookieSession,
    _PyPIVersion,
)
from neuromation.api.login import AuthException, _ClusterConfig
from tests import _TestServerFactory


@pytest.fixture
def tmp_home(tmp_path: Path, monkeypatch: Any) -> Path:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)  # Like as it's not enough
    monkeypatch.setenv("HOME", str(tmp_path))

    return tmp_path


@pytest.fixture
def config_file(
    tmp_home: Path, token: str, auth_config: _AuthConfig, cluster_config: _ClusterConfig
) -> Path:
    config_path = tmp_home / ".nmrc"
    _create_config(config_path, token, auth_config, cluster_config)
    return config_path


@pytest.fixture
async def mock_for_login(aiohttp_server: _TestServerFactory, token: str) -> _TestServer:
    async def config_handler(request: web.Request) -> web.Response:
        config_json: Dict[str, Any] = {
            "auth_url": str(srv.make_url("/authorize")),
            "token_url": str(srv.make_url("/oauth/token")),
            "client_id": "banana",
            "audience": "https://test.dev.neuromation.io",
            "headless_callback_url": str(srv.make_url("/oauth/show-code")),
            "callback_urls": [
                "http://127.0.0.2:54540",
                "http://127.0.0.2:54541",
                "http://127.0.0.2:54542",
            ],
            "success_redirect_url": "https://neu.ro/#test",
        }

        if (
            "Authorization" in request.headers
            and "incorrect" not in request.headers["Authorization"]
        ):
            config_json.update(
                {
                    "registry_url": "https://registry-dev.test.com",
                    "storage_url": "https://storage-dev.test.com",
                    "users_url": "https://users-dev.test.com",
                    "monitoring_url": "https://monitoring-dev.test.com",
                    "resource_presets": [
                        {
                            "name": "gpu-small",
                            "cpu": 7,
                            "memory_mb": 30 * 1024,
                            "gpu": 1,
                            "gpu_model": "nvidia-tesla-k80",
                        },
                        {
                            "name": "gpu-large",
                            "cpu": 7,
                            "memory_mb": 60 * 1024,
                            "gpu": 1,
                            "gpu_model": "nvidia-tesla-v100",
                        },
                        {"name": "cpu-small", "cpu": 2, "memory_mb": 2 * 1024},
                        {"name": "cpu-large", "cpu": 3, "memory_mb": 14 * 1024},
                    ],
                }
            )
        return web.json_response(config_json)

    async def show_code(request: web.Request) -> web.Response:
        return web.json_response({})

    async def authorize(request: web.Request) -> web.Response:
        url = URL(request.query["redirect_uri"]).with_query(code="test_auth_code")
        raise web.HTTPSeeOther(location=url)

    async def new_token(request: web.Request) -> web.Response:
        return web.json_response(
            {"access_token": token, "expires_in": 3600, "refresh_token": token}
        )

    app = web.Application()
    app.router.add_get("/config", config_handler)
    app.router.add_get("/oauth/show-code", show_code)
    app.router.add_get("/authorize", authorize)
    app.router.add_post("/oauth/token", new_token)
    srv = await aiohttp_server(app)
    return srv


def _create_config(
    nmrc_path: Path,
    token: str,
    auth_config: _AuthConfig,
    cluster_config: _ClusterConfig,
) -> str:
    config = _Config(
        auth_config=auth_config,
        auth_token=_AuthToken.create_non_expiring(token),
        cluster_config=cluster_config,
        pypi=_PyPIVersion.create_uninitialized(),
        url=URL("https://dev.neu.ro/api/v1"),
        cookie_session=_CookieSession.create_uninitialized(),
        version=neuromation.__version__,
    )
    Factory(nmrc_path)._save(config)
    assert nmrc_path.exists()
    return token


class TestConfigFileInteraction:
    async def test_config_file_absent(self, tmp_home: Path) -> None:
        with pytest.raises(ConfigError, match=r"file.+not exists"):
            await Factory().get()

    async def test_config_file_is_dir(self, tmp_home: Path) -> None:
        Path(tmp_home / ".nmrc").mkdir()
        with pytest.raises(ConfigError, match=r"not a regular file"):
            await Factory().get()

    async def test_default_path(
        self,
        tmp_home: Path,
        token: str,
        auth_config: _AuthConfig,
        cluster_config: _ClusterConfig,
    ) -> None:
        token = _create_config(tmp_home / ".nmrc", token, auth_config, cluster_config)
        client = await Factory().get()
        await client.close()
        assert client._config.auth_token.token == token

    async def test_preset_serialization(
        self,
        tmp_home: Path,
        token: str,
        auth_config: _AuthConfig,
        cluster_config: _ClusterConfig,
    ) -> None:
        _create_config(tmp_home / ".nmrc", token, auth_config, cluster_config)
        client = await Factory().get()
        await client.close()
        assert len(client.presets) > 0
        assert not client.presets["cpu-large"].is_preemptible
        assert client.presets["cpu-large-p"].is_preemptible

    async def test_shorten_path(
        self,
        tmp_home: Path,
        token: str,
        auth_config: _AuthConfig,
        cluster_config: _ClusterConfig,
    ) -> None:
        token = _create_config(
            tmp_home / "test.nmrc", token, auth_config, cluster_config
        )
        client = await Factory(Path("~/test.nmrc")).get()
        await client.close()
        assert client._config.auth_token.token == token

    async def test_full_path(
        self,
        tmp_home: Path,
        token: str,
        auth_config: _AuthConfig,
        cluster_config: _ClusterConfig,
    ) -> None:
        config_path = tmp_home / "test.nmrc"
        token = _create_config(config_path, token, auth_config, cluster_config)
        client = await Factory(config_path).get()
        await client.close()
        assert client._config.auth_token.token == token

    async def test_token_autorefreshing(
        self, config_file: Path, monkeypatch: Any
    ) -> None:
        new_token = jwt.encode({"identity": "new_user"}, "secret", algorithm="HS256")

        async def _refresh_token_mock(
            connector: aiohttp.ClientSession, config: _AuthConfig, token: _AuthToken
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

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Windows does not supports UNIX-like permissions",
    )
    async def test_file_permissions_suppress_security_check(
        self,
        tmpdir: Path,
        token: str,
        auth_config: _AuthConfig,
        cluster_config: _ClusterConfig,
        monkeypatch: Any,
    ) -> None:
        monkeypatch.setenv(TRUSTED_CONFIG_PATH, "1")
        config_path = Path(tmpdir) / "test.nmrc"
        _create_config(config_path, token, auth_config, cluster_config)
        config_path.chmod(0o644)
        client = await Factory(config_path).get()
        await client.close()
        assert client

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

    async def test_silent_update(
        self, config_file: Path, mock_for_login: _TestServer
    ) -> None:
        # make config
        async def show_dummy_browser(url: URL) -> None:
            async with aiohttp.ClientSession() as client:
                await client.get(url, allow_redirects=True)

        config_file.unlink()

        await Factory(config_file).login(
            show_dummy_browser, url=mock_for_login.make_url("/")
        )
        with config_file.open("r") as f:
            config = yaml.safe_load(f)
        config["version"] = "10.1.1"  # config belongs old version
        config["url"] = str(mock_for_login.make_url("/"))
        with config_file.open("w") as f:
            yaml.safe_dump(config, f)
        client = await Factory(config_file).get()
        await client.close()

        with config_file.open("r") as f:
            config = yaml.safe_load(f)
        assert config["version"] == neuromation.__version__

    async def test_explicit_update(
        self, config_file: Path, mock_for_login: _TestServer
    ) -> None:
        # await Factory().login(url=mock_for_login)
        # config_file = tmp_home / ".nmrc"
        with config_file.open("r") as f:
            config = yaml.safe_load(f)
        config["version"] = "10.1.1"  # config belongs old version
        config["url"] = str(mock_for_login.make_url("/"))
        with config_file.open("w") as f:
            yaml.safe_dump(config, f)
        with pytest.raises(ConfigError, match="Neuro Platform CLI updated"):
            await Factory(config_file).get()


class TestLogin:
    async def show_dummy_browser(self, url: URL) -> None:
        async with aiohttp.ClientSession() as client:
            await client.get(url, allow_redirects=True)

    async def test_login_already_logged(self, config_file: Path) -> None:
        with pytest.raises(ConfigError, match=r"already exists"):
            await Factory().login(self.show_dummy_browser)

    async def test_normal_login(
        self, tmp_home: Path, mock_for_login: _TestServer
    ) -> None:
        await Factory().login(self.show_dummy_browser, url=mock_for_login.make_url("/"))
        nmrc_path = tmp_home / ".nmrc"
        assert Path(nmrc_path).exists(), "Config file not written after login "
        saved_config = Factory(nmrc_path)._read()
        assert saved_config.auth_config.is_initialized()
        assert saved_config.cluster_config.is_initialized()


class TestLoginWithToken:
    async def test_login_with_token_already_logged(self, config_file: Path) -> None:
        with pytest.raises(ConfigError, match=r"already exists"):
            await Factory().login_with_token(token="tokenstr")

    async def test_normal_login(
        self, tmp_home: Path, mock_for_login: _TestServer
    ) -> None:
        await Factory().login_with_token(
            token="tokenstr", url=mock_for_login.make_url("/")
        )
        nmrc_path = tmp_home / ".nmrc"
        assert Path(nmrc_path).exists(), "Config file not written after login "
        saved_config = Factory(nmrc_path)._read()
        assert saved_config.auth_config.is_initialized()
        assert saved_config.cluster_config.is_initialized()

    async def test_incorrect_token(
        self, tmp_home: Path, mock_for_login: _TestServer
    ) -> None:
        with pytest.raises(AuthException):
            await Factory().login_with_token(
                token="incorrect", url=mock_for_login.make_url("/")
            )
        nmrc_path = tmp_home / ".nmrc"
        assert not Path(nmrc_path).exists(), "Config file not written after login "


class TestHeadlessLogin:
    async def test_login_headless_already_logged(self, config_file: Path) -> None:
        async def get_auth_code_cb(url: URL) -> str:
            return ""

        with pytest.raises(ConfigError, match=r"already exists"):
            await Factory().login_headless(get_auth_code_cb)

    async def test_normal_login(
        self, tmp_home: Path, mock_for_login: _TestServer
    ) -> None:
        async def get_auth_code_cb(url: URL) -> str:
            assert url.with_query(None) == mock_for_login.make_url("/authorize")

            assert dict(url.query) == dict(
                response_type="code",
                code_challenge=mock.ANY,
                code_challenge_method="S256",
                client_id="banana",
                redirect_uri=str(mock_for_login.make_url("/oauth/show-code")),
                scope="offline_access",
                audience="https://test.dev.neuromation.io",
            )
            return "test_code"

        await Factory().login_headless(
            get_auth_code_cb, url=mock_for_login.make_url("/")
        )
        nmrc_path = tmp_home / ".nmrc"
        assert Path(nmrc_path).exists(), "Config file not written after login "
        saved_config = Factory(nmrc_path)._read()
        assert saved_config.auth_config.is_initialized()
        assert saved_config.cluster_config.is_initialized()


class TestLogout:
    async def test_logout(self, config_file: Path) -> None:
        await Factory().logout()
        assert not config_file.exists(), "Config not removed after logout"
