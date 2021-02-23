from decimal import Decimal

import aiohttp
import pytest
from aiohttp import web
from yarl import URL

from neuro_sdk import Cluster, Preset
from neuro_sdk.login import _AuthConfig
from neuro_sdk.server_cfg import _ServerConfig, get_server_config

from tests import _TestClientFactory


async def test_get_server_config_no_clusters(
    aiohttp_client: _TestClientFactory,
) -> None:
    auth_url = "https://dev-neuro.auth0.com/authorize"
    token_url = "https://dev-neuro.auth0.com/oauth/token"
    logout_url = "https://dev-neuro.auth0.com/v2/logout"
    client_id = "this_is_client_id"
    audience = "https://platform.dev.neu.ro"
    headless_callback_url = "https://dev.neu.ro/oauth/show-code"
    callback_urls = [
        "http://127.0.0.1:54540",
        "http://127.0.0.1:54541",
        "http://127.0.0.1:54542",
    ]
    success_redirect_url = "https://platform.neu.ro"
    JSON = {
        "auth_url": auth_url,
        "token_url": token_url,
        "logout_url": logout_url,
        "client_id": client_id,
        "audience": audience,
        "callback_urls": callback_urls,
        "success_redirect_url": success_redirect_url,
        "headless_callback_url": headless_callback_url,
    }

    async def handler(request: web.Request) -> web.Response:
        assert "Authorization" not in request.headers
        return web.json_response(JSON)

    app = web.Application()
    app.router.add_get("/config", handler)
    client = await aiohttp_client(app)

    config = await get_server_config(client.session, client.make_url("/"))
    assert config == _ServerConfig(
        auth_config=_AuthConfig(
            auth_url=URL(auth_url),
            token_url=URL(token_url),
            logout_url=URL(logout_url),
            client_id=client_id,
            audience=audience,
            headless_callback_url=URL(headless_callback_url),
            callback_urls=tuple(URL(u) for u in callback_urls),
            success_redirect_url=URL(success_redirect_url),
        ),
        clusters={},
        admin_url=None,
    )


async def test_get_server_config_no_callback_urls(
    aiohttp_client: _TestClientFactory,
) -> None:

    auth_url = "https://dev-neuro.auth0.com/authorize"
    token_url = "https://dev-neuro.auth0.com/oauth/token"
    logout_url = "https://dev-neuro.auth0.com/v2/logout"
    client_id = "this_is_client_id"
    audience = "https://platform.dev.neu.ro"
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
    }

    async def handler(request: web.Request) -> web.Response:
        assert "Authorization" not in request.headers
        return web.json_response(JSON)

    app = web.Application()
    app.router.add_get("/config", handler)
    client = await aiohttp_client(app)

    config = await get_server_config(client.session, client.make_url("/"))
    assert config == _ServerConfig(
        auth_config=_AuthConfig(
            auth_url=URL(auth_url),
            token_url=URL(token_url),
            logout_url=URL(logout_url),
            client_id=client_id,
            audience=audience,
            headless_callback_url=URL(headless_callback_url),
            success_redirect_url=URL(success_redirect_url),
        ),
        clusters={},
        admin_url=None,
    )


async def test_get_server_config_with_token_legacy(
    aiohttp_client: _TestClientFactory,
) -> None:

    admin_url = "https://admin-dev.neu.ro"
    registry_url = "https://registry.dev.neu.ro"
    storage_url = "https://storage.dev.neu.ro"
    blob_storage_url = "https://blob-storage.dev.neu.ro"
    users_url = "https://dev.neu.ro/users"
    monitoring_url = "https://dev.neu.ro/monitoring"
    secrets_url = "https://dev.neu.ro/secrets"
    disks_url = "https://dev.neu.ro/disks"
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
                "name": "default",
                "monitoring_url": monitoring_url,
                "storage_url": storage_url,
                "blob_storage_url": blob_storage_url,
                "registry_url": registry_url,
                "users_url": users_url,
                "secrets_url": secrets_url,
                "disks_url": disks_url,
                "resource_presets": [
                    {
                        "name": "gpu-small",
                        "credits_per_hour": "10",
                        "cpu": 7,
                        "memory_mb": 30 * 1024,
                        "gpu": 1,
                        "gpu_model": "nvidia-tesla-k80",
                    },
                    {
                        "name": "gpu-large",
                        "credits_per_hour": "10",
                        "cpu": 7,
                        "memory_mb": 60 * 1024,
                        "gpu": 1,
                        "gpu_model": "nvidia-tesla-v100",
                    },
                    {
                        "name": "cpu-small",
                        "credits_per_hour": "10",
                        "cpu": 2,
                        "memory_mb": 2 * 1024,
                    },
                    {
                        "name": "cpu-large",
                        "credits_per_hour": "10",
                        "cpu": 3,
                        "memory_mb": 14 * 1024,
                    },
                    {
                        "name": "cpu-large-p",
                        "credits_per_hour": "10",
                        "cpu": 3,
                        "memory_mb": 14 * 1024,
                        "scheduler_enabled": True,
                        "preemptible_node": True,
                    },
                ],
            }
        ],
    }

    async def handler(request: web.Request) -> web.Response:
        assert request.headers["Authorization"] == "Bearer bananatoken"
        return web.json_response(JSON)

    app = web.Application()
    app.router.add_get("/config", handler)
    client = await aiohttp_client(app)

    config = await get_server_config(
        client.session, client.make_url("/"), token="bananatoken"
    )
    assert config == _ServerConfig(
        auth_config=_AuthConfig(
            auth_url=URL(auth_url),
            token_url=URL(token_url),
            logout_url=URL(logout_url),
            client_id=client_id,
            audience=audience,
            headless_callback_url=URL(headless_callback_url),
            success_redirect_url=URL(success_redirect_url),
        ),
        admin_url=URL(admin_url),
        clusters={
            "default": Cluster(
                registry_url=URL(registry_url),
                storage_url=URL(storage_url),
                blob_storage_url=URL(blob_storage_url),
                users_url=URL(users_url),
                monitoring_url=URL(monitoring_url),
                secrets_url=URL(secrets_url),
                disks_url=URL(disks_url),
                presets={
                    "gpu-small": Preset(
                        credits_per_hour=Decimal("10"),
                        cpu=7,
                        memory_mb=30 * 1024,
                        gpu=1,
                        gpu_model="nvidia-tesla-k80",
                    ),
                    "gpu-large": Preset(
                        credits_per_hour=Decimal("10"),
                        cpu=7,
                        memory_mb=60 * 1024,
                        gpu=1,
                        gpu_model="nvidia-tesla-v100",
                    ),
                    "cpu-small": Preset(
                        credits_per_hour=Decimal("10"), cpu=2, memory_mb=2 * 1024
                    ),
                    "cpu-large": Preset(
                        credits_per_hour=Decimal("10"), cpu=3, memory_mb=14 * 1024
                    ),
                    "cpu-large-p": Preset(
                        credits_per_hour=Decimal("10"),
                        cpu=3,
                        memory_mb=14 * 1024,
                        scheduler_enabled=True,
                        preemptible_node=True,
                    ),
                },
                name="default",
            )
        },
    )


async def test_get_server_config_with_token(aiohttp_client: _TestClientFactory) -> None:

    admin_url = "https://admin-dev.neu.ro"
    registry_url = "https://registry.dev.neu.ro"
    storage_url = "https://storage.dev.neu.ro"
    blob_storage_url = "https://blob-storage.dev.neu.ro"
    users_url = "https://dev.neu.ro/users"
    monitoring_url = "https://dev.neu.ro/monitoring"
    secrets_url = "https://dev.neu.ro/secrets"
    disks_url = "https://dev.neu.ro/disks"
    auth_url = "https://dev-neuro.auth0.com/authorize"
    token_url = "https://dev-neuro.auth0.com/oauth/token"
    logout_url = "https://dev-neuro.auth0.com/v2/logout"
    client_id = "this_is_client_id"
    audience = "https://platform.dev.neuro.io"
    headless_callback_url = "https://dev.neu.ro/oauth/show-code"
    success_redirect_url = "https://platform.neu.ro"
    JSON = {
        "name": "default",
        "admin_url": admin_url,
        "registry_url": registry_url,
        "storage_url": storage_url,
        "users_url": users_url,
        "monitoring_url": monitoring_url,
        "resource_presets": [
            {
                "name": "gpu-small",
                "credits_per_hour": "10",
                "cpu": 7,
                "memory_mb": 30 * 1024,
                "gpu": 1,
                "gpu_model": "nvidia-tesla-k80",
            },
            {
                "name": "gpu-large",
                "credits_per_hour": "10",
                "cpu": 7,
                "memory_mb": 60 * 1024,
                "gpu": 1,
                "gpu_model": "nvidia-tesla-v100",
            },
            {
                "name": "cpu-small",
                "credits_per_hour": "10",
                "cpu": 2,
                "memory_mb": 2 * 1024,
            },
            {
                "name": "cpu-large",
                "credits_per_hour": "10",
                "cpu": 3,
                "memory_mb": 14 * 1024,
            },
        ],
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
                        "name": "gpu-small",
                        "credits_per_hour": "10",
                        "cpu": 7,
                        "memory_mb": 30 * 1024,
                        "gpu": 1,
                        "gpu_model": "nvidia-tesla-k80",
                    },
                    {
                        "name": "gpu-large",
                        "credits_per_hour": "10",
                        "cpu": 7,
                        "memory_mb": 60 * 1024,
                        "gpu": 1,
                        "gpu_model": "nvidia-tesla-v100",
                    },
                    {
                        "name": "cpu-small",
                        "credits_per_hour": "10",
                        "cpu": 2,
                        "memory_mb": 2 * 1024,
                    },
                    {
                        "name": "cpu-large",
                        "credits_per_hour": "10",
                        "cpu": 3,
                        "memory_mb": 14 * 1024,
                    },
                    {
                        "name": "cpu-large-p",
                        "credits_per_hour": "10",
                        "cpu": 3,
                        "memory_mb": 14 * 1024,
                        "scheduler_enabled": True,
                        "preemptible_node": True,
                    },
                ],
            }
        ],
        "auth_url": auth_url,
        "token_url": token_url,
        "logout_url": logout_url,
        "client_id": client_id,
        "audience": audience,
        "callback_urls": [
            "http://127.0.0.1:54540",
            "http://127.0.0.1:54541",
            "http://127.0.0.1:54542",
        ],
        "headless_callback_url": headless_callback_url,
        "success_redirect_url": success_redirect_url,
    }

    async def handler(request: web.Request) -> web.Response:
        assert request.headers["Authorization"] == "Bearer bananatoken"
        return web.json_response(JSON)

    app = web.Application()
    app.router.add_get("/config", handler)
    client = await aiohttp_client(app)

    config = await get_server_config(
        client.session, client.make_url("/"), token="bananatoken"
    )
    cluster_config = Cluster(
        registry_url=URL(registry_url),
        storage_url=URL(storage_url),
        blob_storage_url=URL(blob_storage_url),
        users_url=URL(users_url),
        monitoring_url=URL(monitoring_url),
        secrets_url=URL(secrets_url),
        disks_url=URL(disks_url),
        presets={
            "gpu-small": Preset(
                credits_per_hour=Decimal("10"),
                cpu=7,
                memory_mb=30 * 1024,
                gpu=1,
                gpu_model="nvidia-tesla-k80",
            ),
            "gpu-large": Preset(
                credits_per_hour=Decimal("10"),
                cpu=7,
                memory_mb=60 * 1024,
                gpu=1,
                gpu_model="nvidia-tesla-v100",
            ),
            "cpu-small": Preset(
                credits_per_hour=Decimal("10"), cpu=2, memory_mb=2 * 1024
            ),
            "cpu-large": Preset(
                credits_per_hour=Decimal("10"), cpu=3, memory_mb=14 * 1024
            ),
            "cpu-large-p": Preset(
                credits_per_hour=Decimal("10"),
                cpu=3,
                memory_mb=14 * 1024,
                scheduler_enabled=True,
                preemptible_node=True,
            ),
        },
        name="default",
    )
    assert config == _ServerConfig(
        auth_config=_AuthConfig(
            auth_url=URL(auth_url),
            token_url=URL(token_url),
            logout_url=URL(logout_url),
            client_id=client_id,
            audience=audience,
            headless_callback_url=URL(headless_callback_url),
            success_redirect_url=URL(success_redirect_url),
        ),
        admin_url=URL(admin_url),
        clusters={"default": cluster_config},
    )


async def test_get_server_config__fail(aiohttp_client: _TestClientFactory) -> None:
    async def handler(request: web.Request) -> web.Response:
        raise aiohttp.web.HTTPInternalServerError(reason="unexpected server error")

    app = web.Application()
    app.router.add_get("/config", handler)
    client = await aiohttp_client(app)

    with pytest.raises(RuntimeError, match="Unable to get server configuration: 500"):
        await get_server_config(client.session, client.make_url("/"))
