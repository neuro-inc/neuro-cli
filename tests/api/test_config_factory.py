import sys
from pathlib import Path
from typing import Any, Callable, Dict
from unittest import mock

import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer as _TestServer
from yarl import URL

import neuromation
import neuromation.api.config_factory
from neuromation.api import Cluster, ConfigError, Factory
from neuromation.api.config import _AuthConfig, _AuthToken, _ConfigData
from neuromation.api.login import AuthException
from tests import _TestServerFactory


@pytest.fixture
def tmp_home(tmp_path: Path, monkeypatch: Any) -> Path:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)  # Like as it's not enough
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
        version=neuromation.__version__,
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
            "client_id": "banana",
            "audience": "https://test.dev.neuromation.io",
            "headless_callback_url": str(srv.make_url("/oauth/show-code")),
            "callback_urls": callback_urls,
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
        assert not client.presets["cpu-large"].is_preemptible
        assert client.presets["cpu-large-p"].is_preemptible

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
        with pytest.raises(AuthException):
            await Factory().login_with_token(
                token="incorrect", url=mock_for_login.make_url("/")
            )
        nmrc_path = tmp_home / ".neuro"
        assert not Path(nmrc_path).exists(), "Config file not written after login "


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
                audience="https://test.dev.neuromation.io",
            )
            return "test_code"

        await Factory().login_headless(
            get_auth_code_cb, url=mock_for_login.make_url("/")
        )
        nmrc_path = tmp_home / ".neuro"
        assert Path(nmrc_path).exists(), "Config file not written after login "


class TestLogout:
    async def test_logout(self, config_dir: Path) -> None:
        await Factory().logout()
        assert not config_dir.exists(), "Config not removed after logout\n" + "\n".join(
            [p.name for p in config_dir.iterdir()]
        )
