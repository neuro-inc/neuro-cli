from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Dict
from unittest import mock
from urllib.parse import parse_qsl

import pytest
import toml
from aiohttp import web
from yarl import URL

from neuro_sdk import Client, Cluster, ConfigError, Preset
from neuro_sdk.config import _check_sections, _merge_user_configs, _validate_user_config
from neuro_sdk.login import _AuthToken

from tests import _TestServerFactory

_MakeClient = Callable[..., Client]


class TestMergeUserConfigs:
    def test_empty_dicts(self) -> None:
        assert _merge_user_configs({}, {}) == {}

    def test_empty_newer(self) -> None:
        assert _merge_user_configs({"a": "b"}, {}) == {"a": "b"}

    def test_empty_older(self) -> None:
        assert _merge_user_configs({}, {"a": "b"}) == {"a": "b"}

    def test_not_overlapped(self) -> None:
        assert _merge_user_configs({"a": "b"}, {"c": "d"}) == {"a": "b", "c": "d"}

    def test_merge_subdicts(self) -> None:
        assert _merge_user_configs(
            {"a": {"b": "1", "c": "2"}}, {"a": {"b": "3", "d": "4"}}
        ) == {"a": {"b": "3", "c": "2", "d": "4"}}


class TestUserConfigValidators:
    def test_unsupported_section(self) -> None:
        with pytest.raises(
            ConfigError, match="file.cfg: unsupported config sections: {'other'}"
        ):
            _check_sections({"other": {"key": "val"}}, {"section"}, "file.cfg")

    def test_section_is_not_dict(self) -> None:
        with pytest.raises(
            ConfigError, match="file.cfg: 'a' should be a section, got 1"
        ):
            _check_sections({"a": 1}, {"a"}, "file.cfg")

    def test_invalid_alias_name(self) -> None:
        with pytest.raises(ConfigError, match="file.cfg: invalid alias name 0123"):
            _validate_user_config({"alias": {"0123": "ls"}}, "file.cfg")

    def test_invalid_alias_type(self) -> None:
        with pytest.raises(ConfigError, match="file.cfg: invalid alias command type"):
            _validate_user_config({"alias": {"new-name": True}}, "file.cfg")

    def test_extra_session_param(self) -> None:
        with pytest.raises(
            ConfigError, match="file.cfg: unknown parameters job.unknown-name"
        ):
            _validate_user_config({"job": {"unknown-name": True}}, "file.cfg")

    def test_invalid_param_type(self) -> None:
        with pytest.raises(
            ConfigError,
            match="file.cfg: invalid type for job.ps-format, str is expected",
        ):
            _validate_user_config({"job": {"ps-format": True}}, "file.cfg")

    def test_invalid_complex_type(self) -> None:
        with pytest.raises(
            ConfigError,
            match="file.cfg: invalid type for storage.cp-exclude, list is expected",
        ):
            _validate_user_config({"storage": {"cp-exclude": "abc"}}, "file.cfg")

    def test_invalid_complex_item_type(self) -> None:
        with pytest.raises(
            ConfigError,
            match=(
                r"file.cfg: invalid type for storage.cp-exclude\[0\], "
                "str is expected"
            ),
        ):
            _validate_user_config({"storage": {"cp-exclude": [1, 2]}}, "file.cfg")

    def test_not_allowed_cluster_name(self) -> None:
        with pytest.raises(ConfigError, match=r"file.cfg: cluster name is not allowed"):
            _validate_user_config({"job": {"cluster-name": "another"}}, "file.cfg")


async def test_get_user_config_empty(make_client: _MakeClient) -> None:
    async with make_client("https://example.com") as client:
        assert await client.config.get_user_config() == {}


async def test_get_user_config_from_global(make_client: _MakeClient) -> None:
    async with make_client("https://example.com") as client:
        client.config._path.mkdir(parents=True, exist_ok=True)
        global_conf = client.config._path / "user.toml"
        # FIXME: the example may be broken in future versions
        global_conf.write_text(
            toml.dumps({"alias": {"pss": {"cmd": "job ps --short"}}})
        )
        assert await client.config.get_user_config() == {
            "alias": {"pss": {"cmd": "job ps --short"}}
        }


async def test_get_user_config_from_local(
    monkeypatch: Any, tmp_path: Path, make_client: _MakeClient
) -> None:
    async with make_client("https://example.com") as client:
        proj_dir = tmp_path / "project"
        local_dir = proj_dir / "folder"
        local_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.chdir(local_dir)
        local_conf = proj_dir / ".neuro.toml"
        # FIXME: the example may be broken in future versions
        local_conf.write_text(toml.dumps({"alias": {"pss": {"cmd": "job ps --short"}}}))
        assert await client.config.get_user_config() == {
            "alias": {"pss": {"cmd": "job ps --short"}}
        }


@pytest.fixture
def multiple_clusters_config() -> Dict[str, Cluster]:
    return {
        "default": Cluster(
            name="default",
            registry_url=URL("https://registry-dev.neu.ro"),
            storage_url=URL("https://storage-dev.neu.ro"),
            blob_storage_url=URL("https://blob-storage-dev.neu.ro"),
            users_url=URL("https://users-dev.neu.ro"),
            monitoring_url=URL("https://jobs-dev.neu.ro"),
            secrets_url=URL("https://secrets-dev.neu.ro"),
            disks_url=URL("https://disks-dev.neu.ro"),
            presets={
                "cpu-small": Preset(
                    credits_per_hour=Decimal("10"), cpu=1, memory_mb=2 * 1024
                )
            },
        ),
        "another": Cluster(
            name="another",
            registry_url=URL("https://registry2-dev.neu.ro"),
            storage_url=URL("https://storage2-dev.neu.ro"),
            blob_storage_url=URL("https://blob-storage-dev.neu.ro"),
            users_url=URL("https://users2-dev.neu.ro"),
            monitoring_url=URL("https://jobs2-dev.neu.ro"),
            secrets_url=URL("https://secrets2-dev.neu.ro"),
            disks_url=URL("https://disks-dev.neu.ro"),
            presets={
                "cpu-large": Preset(
                    credits_per_hour=Decimal("10"), cpu=7, memory_mb=14 * 1024
                )
            },
        ),
    }


async def test_get_cluster_name_from_local(
    monkeypatch: Any,
    tmp_path: Path,
    make_client: _MakeClient,
    multiple_clusters_config: Dict[str, Cluster],
) -> None:
    async with make_client(
        "https://example.org", clusters=multiple_clusters_config
    ) as client:
        proj_dir = tmp_path / "project"
        local_dir = proj_dir / "folder"
        local_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.chdir(local_dir)
        assert client.config.cluster_name == "default"
        assert client.config.registry_url == URL("https://registry-dev.neu.ro")
        assert client.config.storage_url == URL("https://storage-dev.neu.ro")
        assert client.config.blob_storage_url == URL("https://blob-storage-dev.neu.ro")
        assert client.config.monitoring_url == URL("https://jobs-dev.neu.ro")
        assert client.config.secrets_url == URL("https://secrets-dev.neu.ro")
        assert client.config.presets == {
            "cpu-small": Preset(
                credits_per_hour=Decimal("10"), cpu=1, memory_mb=2 * 1024
            )
        }

        local_conf = proj_dir / ".neuro.toml"
        local_conf.write_text(toml.dumps({"job": {"cluster-name": "another"}}))
        assert client.config.cluster_name == "another"
        assert client.config.registry_url == URL("https://registry2-dev.neu.ro")
        assert client.config.storage_url == URL("https://storage2-dev.neu.ro")
        assert client.config.monitoring_url == URL("https://jobs2-dev.neu.ro")
        assert client.config.secrets_url == URL("https://secrets2-dev.neu.ro")
        assert client.config.presets == {
            "cpu-large": Preset(
                credits_per_hour=Decimal("10"), cpu=7, memory_mb=14 * 1024
            )
        }


async def test_get_cluster_name_from_local_invalid_cluster(
    monkeypatch: Any,
    tmp_path: Path,
    make_client: _MakeClient,
    multiple_clusters_config: Dict[str, Cluster],
) -> None:
    async with make_client("https://example.org") as client:
        proj_dir = tmp_path / "project"
        local_dir = proj_dir / "folder"
        local_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.chdir(local_dir)
        assert client.config.cluster_name == "default"

        local_conf = proj_dir / ".neuro.toml"
        local_conf.write_text(toml.dumps({"job": {"cluster-name": "unknown"}}))
        assert client.config.cluster_name == "unknown"
        match = "Cluster unknown doesn't exist.*Please edit local user config file"
        with pytest.raises(RuntimeError, match=match):
            client.config.registry_url
        with pytest.raises(RuntimeError, match=match):
            client.config.storage_url
        with pytest.raises(RuntimeError, match=match):
            client.config.monitoring_url
        with pytest.raises(RuntimeError, match=match):
            client.config.secrets_url
        with pytest.raises(RuntimeError, match=match):
            client.config.presets


async def test_username(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    app = web.Application()
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        assert client.config.username == "user"


async def test_presets(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    app = web.Application()
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        assert client.config.presets == {
            "cpu-large": Preset(
                credits_per_hour=Decimal("10"),
                cpu=7,
                memory_mb=14336,
                scheduler_enabled=False,
                gpu=None,
                gpu_model=None,
                tpu_type=None,
                tpu_software_version=None,
            ),
            "cpu-small": Preset(
                credits_per_hour=Decimal("10"),
                cpu=7,
                memory_mb=2048,
                scheduler_enabled=False,
                gpu=None,
                gpu_model=None,
                tpu_type=None,
                tpu_software_version=None,
            ),
            "gpu-large": Preset(
                credits_per_hour=Decimal("10"),
                cpu=7,
                memory_mb=61440,
                scheduler_enabled=False,
                gpu=1,
                gpu_model="nvidia-tesla-v100",
                tpu_type=None,
                tpu_software_version=None,
            ),
            "gpu-small": Preset(
                credits_per_hour=Decimal("10"),
                cpu=7,
                memory_mb=30720,
                scheduler_enabled=False,
                gpu=1,
                gpu_model="nvidia-tesla-k80",
                tpu_type=None,
                tpu_software_version=None,
            ),
        }


async def test_cluster_name(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    app = web.Application()
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        assert client.config.cluster_name == "default"


async def test_clusters(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    app = web.Application()
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        assert dict(client.config.clusters) == {
            "default": Cluster(
                name="default",
                registry_url=URL("https://registry-dev.neu.ro"),
                storage_url=srv.make_url("/storage"),
                blob_storage_url=srv.make_url("/blob"),
                users_url=srv.make_url("/"),
                monitoring_url=srv.make_url("/jobs"),
                secrets_url=srv.make_url("/secrets"),
                disks_url=srv.make_url("/disk"),
                presets=mock.ANY,
            ),
            "another": Cluster(
                name="another",
                registry_url=srv.make_url("/registry2"),
                storage_url=srv.make_url("/storage2"),
                blob_storage_url=srv.make_url("/blob2"),
                users_url=srv.make_url("/"),
                monitoring_url=srv.make_url("/jobs2"),
                secrets_url=srv.make_url("/secrets2"),
                disks_url=srv.make_url("/disk2"),
                presets=mock.ANY,
            ),
        }


async def test_fetch(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    admin_url = "https://admin-dev.neu.ro"
    registry_url = "https://registry2-dev.neu.ro"
    storage_url = "https://storage2-dev.neu.ro"
    blob_storage_url = "https://blob-storage2-dev.neu.ro"
    users_url = "https://users2-dev.neu.ro"
    monitoring_url = "https://jobs2-dev.neu.ro"
    secrets_url = "https://secrets2-dev.neu.ro"
    disks_url = "https://disks2-dev.neu.ro"
    auth_url = "https://dev-neuro.auth0.com/authorize"
    token_url = "https://dev-neuro.auth0.com/oauth/token"
    logout_url = "https://dev-neuro.auth0.com/v2/logout"
    client_id = "this_is_client_id"
    audience = "https://platform.dev.neu.ro."
    headless_callback_url = "https://dev.neu.ro/oauth/show-code"
    success_redirect_url = "https://platform.neu.ro"
    JSON = {
        "auth_url": auth_url,
        "token_url": token_url,
        "logout_url": logout_url,
        "client_id": client_id,
        "audience": audience,
        "headless_callback_url": headless_callback_url,
        "success_redirect_url": success_redirect_url,
        "admin_url": admin_url,
        "clusters": [
            {
                "name": "default",
                "registry_url": registry_url,
                "storage_url": storage_url,
                "blob_storage_url": blob_storage_url,
                "users_url": users_url,
                "monitoring_url": monitoring_url,
                "secrets_url": secrets_url,
                "disks_url": disks_url,
                "resource_presets": [
                    {
                        "name": "cpu-small",
                        "credits_per_hour": "10",
                        "cpu": 2,
                        "memory_mb": 2 * 1024,
                    }
                ],
            }
        ],
    }

    async def handler(request: web.Request) -> web.Response:
        return web.json_response(JSON)

    app = web.Application()
    app.add_routes([web.get("/config", handler)])
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        await client.config.fetch()
        assert client.config.clusters == {
            "default": Cluster(
                name="default",
                registry_url=URL(registry_url),
                storage_url=URL(storage_url),
                blob_storage_url=URL(blob_storage_url),
                users_url=URL(users_url),
                monitoring_url=URL(monitoring_url),
                secrets_url=URL(secrets_url),
                disks_url=URL(disks_url),
                presets={
                    "cpu-small": Preset(
                        credits_per_hour=Decimal("10"),
                        cpu=2,
                        memory_mb=2048,
                        scheduler_enabled=False,
                        gpu=None,
                        gpu_model=None,
                        tpu_type=None,
                        tpu_software_version=None,
                    )
                },
            )
        }


async def test_fetch_dropped_selected_cluster(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    # the test returns the same as for valid answer but the cluster name is different
    admin_url = "https://admin-dev.neu.ro"
    registry_url = "https://registry2-dev.neu.ro"
    storage_url = "https://storage2-dev.neu.ro"
    blob_storage_url = "https://blob-storage2-dev.neu.ro"
    users_url = "https://users2-dev.neu.ro"
    monitoring_url = "https://jobs2-dev.neu.ro"
    secrets_url = "https://secrets2-dev.neu.ro"
    disks_url = "https://disks2-dev.neu.ro"
    auth_url = "https://dev-neuro.auth0.com/authorize"
    token_url = "https://dev-neuro.auth0.com/oauth/token"
    logout_url = "https://dev-neuro.auth0.com/v2/logout"
    client_id = "this_is_client_id"
    audience = "https://platform.dev.neuro.io"
    headless_callback_url = "https://dev.neu.ro/oauth/show-code"
    success_redirect_url = "https://platform.neu.ro"
    JSON = {
        "admin_url": admin_url,
        "auth_url": auth_url,
        "token_url": token_url,
        "logout_url": logout_url,
        "client_id": client_id,
        "audience": audience,
        "headless_callback_url": headless_callback_url,
        "success_redirect_url": success_redirect_url,
        "clusters": [
            {
                "name": "another",
                "registry_url": registry_url,
                "storage_url": storage_url,
                "blob_storage_url": blob_storage_url,
                "users_url": users_url,
                "monitoring_url": monitoring_url,
                "secrets_url": secrets_url,
                "disks_url": disks_url,
                "resource_presets": [
                    {
                        "name": "cpu-small",
                        "credits_per_hour": "10",
                        "cpu": 2,
                        "memory_mb": 2 * 1024,
                    }
                ],
            }
        ],
    }

    async def handler(request: web.Request) -> web.Response:
        return web.json_response(JSON)

    app = web.Application()
    app.add_routes([web.get("/config", handler)])
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        with pytest.raises(RuntimeError, match="Cluster default doesn't exist"):
            await client.config.fetch()


async def test_switch_clusters(
    make_client: _MakeClient, multiple_clusters_config: Dict[str, Cluster]
) -> None:
    async with make_client(
        "https://example.org", clusters=multiple_clusters_config
    ) as client:
        assert client.config.cluster_name == "default"
        await client.config.switch_cluster("another")
        assert client.config.cluster_name == "another"


async def test_switch_clusters_unknown(make_client: _MakeClient) -> None:
    async with make_client("https://example.org") as client:
        assert client.config.cluster_name == "default"
        with pytest.raises(RuntimeError, match="Cluster unknown doesn't exist"):
            await client.config.switch_cluster("unknown")
        assert client.config.cluster_name == "default"


async def test_switch_clusters_local(
    monkeypatch: Any,
    tmp_path: Path,
    make_client: _MakeClient,
    multiple_clusters_config: Dict[str, Cluster],
) -> None:
    async with make_client(
        "https://example.org", clusters=multiple_clusters_config
    ) as client:
        proj_dir = tmp_path / "project"
        local_dir = proj_dir / "folder"
        local_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.chdir(local_dir)
        local_conf = proj_dir / ".neuro.toml"
        local_conf.write_text(toml.dumps({"job": {"cluster-name": "another"}}))
        assert client.config.cluster_name == "another"
        with pytest.raises(RuntimeError, match=r"\.neuro\.toml"):
            await client.config.switch_cluster("default")
        assert client.config.cluster_name == "another"


async def test_check_server_mismatch_clusters(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    # the test returns the same as for valid answer but the cluster name is different

    admin_url = "https://admin-dev.neu.ro"
    registry_url = "https://registry2-dev.neu.ro"
    storage_url = "https://storage2-dev.neu.ro"
    blob_storage_url = "https://blob-storage2-dev.neu.ro"
    users_url = "https://users2-dev.neu.ro"
    monitoring_url = "https://jobs2-dev.neu.ro"
    secrets_url = "https://secrets2-dev.neu.ro"
    disks_url = "https://disks2-dev.neu.ro"
    auth_url = "https://dev-neuro.auth0.com/authorize"
    token_url = "https://dev-neuro.auth0.com/oauth/token"
    logout_url = "https://dev-neuro.auth0.com/v2/logout"
    client_id = "this_is_client_id"
    audience = "https://platform.dev.neu.ro"
    headless_callback_url = "https://dev.neu.ro/oauth/show-code"
    success_redirect_url = "https://platform.neu.ro"
    JSON = {
        "admin_url": admin_url,
        "auth_url": auth_url,
        "token_url": token_url,
        "logout_url": logout_url,
        "client_id": client_id,
        "audience": audience,
        "headless_callback_url": headless_callback_url,
        "success_redirect_url": success_redirect_url,
        "clusters": [
            {
                "name": "another",
                "registry_url": registry_url,
                "storage_url": storage_url,
                "blob_storage_url": blob_storage_url,
                "users_url": users_url,
                "monitoring_url": monitoring_url,
                "secrets_url": secrets_url,
                "disks_url": disks_url,
                "resource_presets": [
                    {
                        "name": "cpu-small",
                        "credits_per_hour": "10",
                        "cpu": 2,
                        "memory_mb": 2 * 1024,
                    }
                ],
            }
        ],
    }

    async def handler(request: web.Request) -> web.Response:
        return web.json_response(JSON)

    app = web.Application()
    app.add_routes([web.get("/config", handler)])
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:

        # Set expired version
        client.config._config_data.__dict__["version"] = "18.1.1"

        with pytest.raises(ConfigError, match="Neuro Platform CLI was updated"):
            await client.config.check_server()


async def test_check_server_mismatch_auth(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    # the test returns the same as for valid answer but the cluster name is different

    admin_url = "https://admin-dev.neu.ro"
    registry_url = "https://registry2-dev.neu.ro"
    storage_url = "https://storage2-dev.neu.ro"
    blob_storage_url = "https://blob-storage2-dev.neu.ro"
    users_url = "https://users2-dev.neu.ro"
    monitoring_url = "https://jobs2-dev.neu.ro"
    secrets_url = "https://secrets2-dev.neu.ro"
    disks_url = "https://disks2-dev.neu.ro"
    auth_url = "https://dev-neuro.auth0.com/authorize"
    token_url = "https://dev-neuro.auth0.com/oauth/token"
    logout_url = "https://dev-neuro.auth0.com/v2/logout"
    audience = "https://platform.dev.neu.ro"
    headless_callback_url = "https://dev.neu.ro/oauth/show-code"
    success_redirect_url = "https://platform.neu.ro"
    JSON = {
        "admin_url": admin_url,
        "auth_url": auth_url,
        "token_url": token_url,
        "logout_url": logout_url,
        "client_id": "other_client_id",
        "audience": audience,
        "headless_callback_url": headless_callback_url,
        "success_redirect_url": success_redirect_url,
        "clusters": [
            {
                "name": "default",
                "registry_url": registry_url,
                "storage_url": storage_url,
                "blob_storage_url": blob_storage_url,
                "users_url": users_url,
                "monitoring_url": monitoring_url,
                "secrets_url": secrets_url,
                "disks_url": disks_url,
                "resource_presets": [
                    {
                        "name": "cpu-small",
                        "credits_per_hour": "10",
                        "cpu": 2,
                        "memory_mb": 2 * 1024,
                    }
                ],
            }
        ],
    }

    async def handler(request: web.Request) -> web.Response:
        return web.json_response(JSON)

    app = web.Application()
    app.add_routes([web.get("/config", handler)])
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:

        # Set expired version
        client.config._config_data.__dict__["version"] = "18.1.1"

        with pytest.raises(ConfigError, match="Neuro Platform CLI was updated"):
            await client.config.check_server()


async def test_refresh_token(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient, token: str
) -> None:
    async def handler(request: web.Request) -> web.Response:
        req = dict(parse_qsl(await request.text()))
        assert req == {
            "client_id": "CLIENT-ID",
            "grant_type": "refresh_token",
            "refresh_token": "REFRESH_TOKEN",
        }
        return web.json_response(
            {
                "access_token": "ACCESS_TOKEN",
                "expires_in": 3600,
                "refresh_token": req["refresh_token"],
            }
        )

    app = web.Application()
    app.add_routes([web.post("/oauth/token", handler)])
    srv = await aiohttp_server(app)

    async with make_client(
        srv.make_url("/"), token_url=srv.make_url("/oauth/token")
    ) as client:

        token1 = await client.config.token()

        # Set expired version to far ago
        client.config._config_data.__dict__["auth_token"] = replace(
            _AuthToken.create(token, 3600, "REFRESH_TOKEN"), expiration_time=200
        )

        token2 = await client.config.token()

        assert token1 != token2
        assert token2 == "ACCESS_TOKEN"
