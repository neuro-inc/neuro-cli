import aiohttp
import pytest
from aiohttp import web
from yarl import URL

from neuromation.api import Cluster, Preset
from neuromation.api.login import _AuthConfig
from neuromation.api.server_cfg import _ServerConfig, get_server_config
from tests import _TestClientFactory


async def test_get_server_config_no_clusters(
    aiohttp_client: _TestClientFactory,
) -> None:
    auth_url = "https://dev-neuromation.auth0.com/authorize"
    token_url = "https://dev-neuromation.auth0.com/oauth/token"
    client_id = "this_is_client_id"
    audience = "https://platform.dev.neuromation.io"
    headless_callback_url = "https://dev.neu.ro/oauth/show-code"
    callback_urls = [
        "http://127.0.0.1:54540",
        "http://127.0.0.1:54541",
        "http://127.0.0.1:54542",
    ]
    success_redirect_url = "https://platform.neuromation.io"
    JSON = {
        "auth_url": auth_url,
        "token_url": token_url,
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
            client_id=client_id,
            audience=audience,
            headless_callback_url=URL(headless_callback_url),
            callback_urls=tuple(URL(u) for u in callback_urls),
            success_redirect_url=URL(success_redirect_url),
        ),
        clusters={},
    )


async def test_get_server_config_no_callback_urls(
    aiohttp_client: _TestClientFactory,
) -> None:
    auth_url = "https://dev-neuromation.auth0.com/authorize"
    token_url = "https://dev-neuromation.auth0.com/oauth/token"
    client_id = "this_is_client_id"
    audience = "https://platform.dev.neuromation.io"
    headless_callback_url = "https://dev.neu.ro/oauth/show-code"
    success_redirect_url = "https://platform.neuromation.io"
    JSON = {
        "auth_url": auth_url,
        "token_url": token_url,
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
            client_id=client_id,
            audience=audience,
            headless_callback_url=URL(headless_callback_url),
            success_redirect_url=URL(success_redirect_url),
        ),
        clusters={},
    )


async def test_get_server_config_with_token_legacy(
    aiohttp_client: _TestClientFactory,
) -> None:
    registry_url = "https://registry.dev.neuromation.io"
    storage_url = "https://storage.dev.neuromation.io"
    users_url = "https://dev.neuromation.io/users"
    monitoring_url = "https://dev.neuromation.io/monitoring"
    auth_url = "https://dev-neuromation.auth0.com/authorize"
    token_url = "https://dev-neuromation.auth0.com/oauth/token"
    client_id = "this_is_client_id"
    audience = "https://platform.dev.neuromation.io"
    headless_callback_url = "https://dev.neu.ro/oauth/show-code"
    success_redirect_url = "https://platform.neuromation.io"
    JSON = {
        "registry_url": registry_url,
        "storage_url": storage_url,
        "users_url": users_url,
        "monitoring_url": monitoring_url,
        "auth_url": auth_url,
        "token_url": token_url,
        "client_id": client_id,
        "audience": audience,
        "headless_callback_url": headless_callback_url,
        "success_redirect_url": success_redirect_url,
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
            client_id=client_id,
            audience=audience,
            headless_callback_url=URL(headless_callback_url),
            success_redirect_url=URL(success_redirect_url),
        ),
        clusters={
            "default": Cluster(
                registry_url=URL(registry_url),
                storage_url=URL(storage_url),
                users_url=URL(users_url),
                monitoring_url=URL(monitoring_url),
                presets={
                    "gpu-small": Preset(
                        cpu=7, memory_mb=30 * 1024, gpu=1, gpu_model="nvidia-tesla-k80"
                    ),
                    "gpu-large": Preset(
                        cpu=7, memory_mb=60 * 1024, gpu=1, gpu_model="nvidia-tesla-v100"
                    ),
                    "cpu-small": Preset(cpu=2, memory_mb=2 * 1024),
                    "cpu-large": Preset(cpu=3, memory_mb=14 * 1024),
                },
                name="default",
            )
        },
    )


async def test_get_server_config_with_token(aiohttp_client: _TestClientFactory) -> None:
    registry_url = "https://registry.dev.neuromation.io"
    storage_url = "https://storage.dev.neuromation.io"
    users_url = "https://dev.neuromation.io/users"
    monitoring_url = "https://dev.neuromation.io/monitoring"
    auth_url = "https://dev-neuromation.auth0.com/authorize"
    token_url = "https://dev-neuromation.auth0.com/oauth/token"
    client_id = "this_is_client_id"
    audience = "https://platform.dev.neuromation.io"
    headless_callback_url = "https://dev.neu.ro/oauth/show-code"
    success_redirect_url = "https://platform.neuromation.io"
    JSON = {
        "name": "default",
        "registry_url": registry_url,
        "storage_url": storage_url,
        "users_url": users_url,
        "monitoring_url": monitoring_url,
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
        "clusters": [
            {
                "name": "default",
                "registry_url": registry_url,
                "storage_url": storage_url,
                "users_url": users_url,
                "monitoring_url": monitoring_url,
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
        ],
        "auth_url": auth_url,
        "token_url": token_url,
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
        users_url=URL(users_url),
        monitoring_url=URL(monitoring_url),
        presets={
            "gpu-small": Preset(
                cpu=7, memory_mb=30 * 1024, gpu=1, gpu_model="nvidia-tesla-k80"
            ),
            "gpu-large": Preset(
                cpu=7, memory_mb=60 * 1024, gpu=1, gpu_model="nvidia-tesla-v100"
            ),
            "cpu-small": Preset(cpu=2, memory_mb=2 * 1024),
            "cpu-large": Preset(cpu=3, memory_mb=14 * 1024),
        },
        name="default",
    )
    assert config == _ServerConfig(
        auth_config=_AuthConfig(
            auth_url=URL(auth_url),
            token_url=URL(token_url),
            client_id=client_id,
            audience=audience,
            headless_callback_url=URL(headless_callback_url),
            success_redirect_url=URL(success_redirect_url),
        ),
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
