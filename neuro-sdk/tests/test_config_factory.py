import base64
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict
from unittest import mock

import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer as _TestServer
from yarl import URL

from neuro_sdk import (
    PASS_CONFIG_ENV_NAME,
    AuthError,
    Cluster,
    ConfigError,
    Factory,
    __version__,
)
from neuro_sdk.config import _AuthConfig, _AuthToken, _ConfigData

from tests import _TestServerFactory


@pytest.fixture
def tmp_home(tmp_path: Path, monkeypatch: Any) -> Path:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)  # Like as it's not enough
    if os.name == "nt" and sys.version_info >= (3, 8):
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
    else:
        monkeypatch.setenv("HOME", str(tmp_path))

    return tmp_path


@pytest.fixture
def config_dir(
    tmp_home: Path, token: str, auth_config: _AuthConfig, cluster_config: Cluster
) -> Path:
    config_path = tmp_home / ".neuro"
    _create_config(config_path, token, auth_config, cluster_config)
    return config_path


def _create_config(
    nmrc_path: Path, token: str, auth_config: _AuthConfig, cluster_config: Cluster
) -> str:
    config = _ConfigData(
        auth_config=auth_config,
        auth_token=_AuthToken.create_non_expiring(token),
        url=URL("https://dev.neu.ro/api/v1"),
        admin_url=URL("https://dev.neu.ro/apis/admin/v1"),
        version=__version__,
        cluster_name=cluster_config.name,
        clusters={cluster_config.name: cluster_config},
    )
    Factory(nmrc_path)._save(config)
    assert nmrc_path.exists()
    return token


@pytest.fixture
async def mock_for_login(
    aiohttp_server: _TestServerFactory,
    token: str,
    aiohttp_unused_port: Callable[[], int],
) -> _TestServer:

    callback_urls = [
        f"http://127.0.0.1:{aiohttp_unused_port()}",
        f"http://127.0.0.1:{aiohttp_unused_port()}",
        f"http://127.0.0.1:{aiohttp_unused_port()}",
    ]

    async def config_handler(request: web.Request) -> web.Response:
        config_json: Dict[str, Any] = {
            "auth_url": str(srv.make_url("/authorize")),
            "token_url": str(srv.make_url("/oauth/token")),
            "logout_url": str(srv.make_url("/v2/logout")),
            "admin_url": str(srv.make_url("/apis/admin/v1")),
            "client_id": "banana",
            "audience": "https://test.dev.neu.ro",
            "headless_callback_url": str(srv.make_url("/oauth/show-code")),
            "callback_urls": callback_urls,
            "success_redirect_url": "http://example.com",
        }

        if (
            "Authorization" in request.headers
            and "incorrect" not in request.headers["Authorization"]
        ):
            config_json.update(
                {
                    "clusters": [
                        {
                            "name": "default",
                            "registry_url": "https://registry-dev.test.com",
                            "storage_url": "https://storage-dev.test.com",
                            "blob_storage_url": "https://blob-storage-dev.test.com",
                            "users_url": "https://users-dev.test.com",
                            "monitoring_url": "https://monitoring-dev.test.com",
                            "secrets_url": "https://secrets-dev.test.com",
                            "disks_url": "https://disks-dev.test.com",
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
                    ]
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


class TestConfigFileInteraction:
    async def test_config_file_absent(self, tmp_home: Path) -> None:
        with pytest.raises(ConfigError, match=r"file.+not exists"):
            await Factory().get()

    async def test_config_dir_is_file(self, tmp_home: Path) -> None:
        Path(tmp_home / ".neuro").write_text("something")
        with pytest.raises(ConfigError, match=r"not a directory"):
            await Factory().get()

    async def test_config_file_is_dir(self, tmp_home: Path) -> None:
        path = Path(tmp_home / ".neuro")
        path.mkdir()
        (path / "db").mkdir()
        with pytest.raises(ConfigError, match=r"not a regular file"):
            await Factory().get()

    async def test_default_path(
        self,
        tmp_home: Path,
        token: str,
        auth_config: _AuthConfig,
        cluster_config: Cluster,
    ) -> None:
        token = _create_config(tmp_home / ".neuro", token, auth_config, cluster_config)
        client = await Factory().get()
        await client.close()
        assert await client.config.token() == token

    async def test_preset_serialization(
        self,
        tmp_home: Path,
        token: str,
        auth_config: _AuthConfig,
        cluster_config: Cluster,
    ) -> None:
        _create_config(tmp_home / ".neuro", token, auth_config, cluster_config)
        client = await Factory().get()
        await client.close()
        assert len(client.presets) > 0
        assert not client.presets["cpu-large"].scheduler_enabled
        assert not client.presets["cpu-large"].preemptible_node
        assert client.presets["cpu-large-p"].scheduler_enabled
        assert client.presets["cpu-large-p"].preemptible_node

    async def test_shorten_path(
        self,
        tmp_home: Path,
        token: str,
        auth_config: _AuthConfig,
        cluster_config: Cluster,
    ) -> None:
        token = _create_config(
            tmp_home / "test.nmrc", token, auth_config, cluster_config
        )
        client = await Factory(Path("~/test.nmrc")).get()
        await client.close()
        assert await client.config.token() == token

    async def test_full_path(
        self,
        tmp_home: Path,
        token: str,
        auth_config: _AuthConfig,
        cluster_config: Cluster,
    ) -> None:
        config_path = tmp_home / "test.nmrc"
        token = _create_config(config_path, token, auth_config, cluster_config)
        client = await Factory(config_path).get()
        await client.close()
        assert await client.config.token() == token

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Windows does not supports UNIX-like permissions",
    )
    async def test_file_permissions(self, config_dir: Path) -> None:
        Path(config_dir).chmod(0o777)
        with pytest.raises(ConfigError, match=r"permission"):
            await Factory().get()


class TestLogin:
    async def show_dummy_browser(self, url: URL) -> None:
        async with aiohttp.ClientSession() as client:
            await client.get(url, allow_redirects=True)

    async def test_login_already_logged(self, config_dir: Path) -> None:
        with pytest.raises(ConfigError, match=r"already exists"):
            await Factory().login(self.show_dummy_browser)

    async def test_normal_login(
        self, tmp_home: Path, mock_for_login: _TestServer
    ) -> None:
        await Factory().login(self.show_dummy_browser, url=mock_for_login.make_url("/"))
        nmrc_path = tmp_home / ".neuro"
        assert Path(nmrc_path).exists(), "Config file not written after login "


class TestLoginWithToken:
    async def test_login_with_token_already_logged(self, config_dir: Path) -> None:
        with pytest.raises(ConfigError, match=r"already exists"):
            await Factory().login_with_token(token="tokenstr")

    async def test_normal_login(
        self, tmp_home: Path, mock_for_login: _TestServer
    ) -> None:
        await Factory().login_with_token(
            token="tokenstr", url=mock_for_login.make_url("/")
        )
        nmrc_path = tmp_home / ".neuro"
        assert Path(nmrc_path).exists(), "Config file not written after login "

    async def test_incorrect_token(
        self, tmp_home: Path, mock_for_login: _TestServer
    ) -> None:
        with pytest.raises(AuthError):
            await Factory().login_with_token(
                token="incorrect", url=mock_for_login.make_url("/")
            )
        nmrc_path = tmp_home / ".neuro"
        assert not Path(nmrc_path).exists(), "Config file not written after login "


class TestLoginPassedConfig:
    @pytest.fixture()
    def make_conf_data(self, mock_for_login: _TestServer) -> Callable[[str], str]:
        def _make_config(token: str) -> str:
            data = {
                "token": token,
                "cluster": "default",
                "url": str(mock_for_login.make_url("/")),
            }
            return base64.b64encode(json.dumps(data).encode()).decode()

        return _make_config

    @pytest.fixture()
    def set_conf_to_env(
        self, monkeypatch: Any, make_conf_data: Callable[[str], str]
    ) -> Callable[[str], None]:
        def _set_env(token: str) -> None:
            config_data = make_conf_data(token)
            monkeypatch.setenv(PASS_CONFIG_ENV_NAME, config_data)

        return _set_env

    async def test_login_with_passed_config_already_logged(
        self, set_conf_to_env: Callable[[str], None], config_dir: Path
    ) -> None:
        set_conf_to_env("tokenstr")
        with pytest.raises(ConfigError, match=r"already exists"):
            await Factory().login_with_passed_config()

    async def test_auto_login(
        self, tmp_home: Path, set_conf_to_env: Callable[[str], None]
    ) -> None:
        set_conf_to_env("tokenstr")
        client = await Factory().get()
        await client.close()
        nmrc_path = tmp_home / ".neuro"
        assert Path(nmrc_path).exists(), "Config file not written after login "

    async def test_auto_login_fail(
        self, tmp_home: Path, set_conf_to_env: Callable[[str], None]
    ) -> None:
        set_conf_to_env("incorrect")
        with pytest.raises(AuthError):
            await Factory().get()
        nmrc_path = tmp_home / ".neuro"
        assert not Path(nmrc_path).exists(), "Config file not written after login "

    async def test_normal_login(
        self, tmp_home: Path, set_conf_to_env: Callable[[str], None]
    ) -> None:
        set_conf_to_env("tokenstr")
        await Factory().login_with_passed_config()
        nmrc_path = tmp_home / ".neuro"
        assert Path(nmrc_path).exists(), "Config file not written after login "

    async def test_normal_login_direct_token(
        self, tmp_home: Path, make_conf_data: Callable[[str], str]
    ) -> None:
        token_data = make_conf_data("tokenstr")
        await Factory().login_with_passed_config(token_data)
        nmrc_path = tmp_home / ".neuro"
        assert Path(nmrc_path).exists(), "Config file not written after login "

    async def test_incorrect_token(
        self, tmp_home: Path, set_conf_to_env: Callable[[str], None]
    ) -> None:
        set_conf_to_env("incorrect")
        with pytest.raises(AuthError):
            await Factory().login_with_passed_config()
        nmrc_path = tmp_home / ".neuro"
        assert not Path(nmrc_path).exists(), "Config file written after bad login "

    async def test_bad_data(
        self,
        tmp_home: Path,
        monkeypatch: Any,
    ) -> None:
        monkeypatch.setenv(PASS_CONFIG_ENV_NAME, "something")
        with pytest.raises(ConfigError):
            await Factory().login_with_passed_config()
        nmrc_path = tmp_home / ".neuro"
        assert not Path(nmrc_path).exists(), "Config file written after bad login "

    async def test_no_data(
        self,
        tmp_home: Path,
        monkeypatch: Any,
    ) -> None:
        with pytest.raises(ConfigError):
            await Factory().login_with_passed_config()
        nmrc_path = tmp_home / ".neuro"
        assert not Path(nmrc_path).exists(), "Config file written after bad login "


class TestHeadlessLogin:
    async def test_login_headless_already_logged(self, config_dir: Path) -> None:
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
                audience="https://test.dev.neu.ro",
            )
            return "test_code"

        await Factory().login_headless(
            get_auth_code_cb, url=mock_for_login.make_url("/")
        )
        nmrc_path = tmp_home / ".neuro"
        assert Path(nmrc_path).exists(), "Config file not written after login "


class TestLogout:
    async def test_logout_no_browser_callback(self, config_dir: Path) -> None:
        await Factory().logout()
        assert not config_dir.exists(), "Config not removed after logout\n" + "\n".join(
            [p.name for p in config_dir.iterdir()]
        )

    async def test_logout_with_browser_callback(
        self, auth_config: _AuthConfig, config_dir: Path
    ) -> None:
        async def show_browser(url: URL) -> None:
            expected_logout_url = auth_config.logout_url.with_query(
                client_id=auth_config.client_id
            )
            assert url == expected_logout_url

        await Factory().logout(show_browser)
        assert not config_dir.exists(), "Config not removed after logout\n" + "\n".join(
            [p.name for p in config_dir.iterdir()]
        )
