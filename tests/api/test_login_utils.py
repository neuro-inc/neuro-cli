import aiohttp
import pytest
from aiohttp import web
from yarl import URL

from neuromation.api.login import (
    _AuthConfig,
    _ClusterConfig,
    _ServerConfig,
    get_server_config,
)
from tests import _TestServerFactory


async def test_get_server_config(aiohttp_server: _TestServerFactory) -> None:
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
    srv = await aiohttp_server(app)

    async with aiohttp.TCPConnector() as connector:
        config = await get_server_config(connector, srv.make_url("/"))
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
        cluster_config=_ClusterConfig.create(
            registry_url=URL(), storage_url=URL(), users_url=URL(), monitoring_url=URL()
        ),
    )


async def test_get_server_config_no_callback_urls(
    aiohttp_server: _TestServerFactory
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
    srv = await aiohttp_server(app)

    async with aiohttp.TCPConnector() as connector:
        config = await get_server_config(connector, srv.make_url("/"))
    assert config == _ServerConfig(
        auth_config=_AuthConfig(
            auth_url=URL(auth_url),
            token_url=URL(token_url),
            client_id=client_id,
            audience=audience,
            headless_callback_url=URL(headless_callback_url),
            success_redirect_url=URL(success_redirect_url),
        ),
        cluster_config=_ClusterConfig(
            registry_url=URL(), storage_url=URL(), users_url=URL(), monitoring_url=URL()
        ),
    )


async def test_get_server_config_with_token(aiohttp_server: _TestServerFactory) -> None:
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
    }

    async def handler(request: web.Request) -> web.Response:
        assert request.headers["Authorization"] == "Bearer bananatoken"
        return web.json_response(JSON)

    app = web.Application()
    app.router.add_get("/config", handler)
    srv = await aiohttp_server(app)

    async with aiohttp.TCPConnector() as connector:
        config = await get_server_config(
            connector, srv.make_url("/"), token="bananatoken"
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
        cluster_config=_ClusterConfig.create(
            registry_url=URL(registry_url),
            storage_url=URL(storage_url),
            users_url=URL(users_url),
            monitoring_url=URL(monitoring_url),
        ),
    )


async def test_get_server_config__fail(aiohttp_server: _TestServerFactory) -> None:
    async def handler(request: web.Request) -> web.Response:
        raise aiohttp.web.HTTPInternalServerError(reason="unexpected server error")

    app = web.Application()
    app.router.add_get("/config", handler)
    srv = await aiohttp_server(app)

    with pytest.raises(RuntimeError, match="Unable to get server configuration: 500"):
        async with aiohttp.TCPConnector() as connector:
            await get_server_config(connector, srv.make_url("/"))
