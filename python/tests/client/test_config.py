import aiohttp
import pytest
from aiohttp import web
from yarl import URL

from neuromation.cli.login import AuthConfig
from neuromation.client import IllegalArgumentError
from neuromation.client.config import ServerConfig, get_server_config


async def test_get_server_config(aiohttp_server):
    registry_url = "http://registry.dev.neuromation.io"
    auth_url = "https://dev-neuromation.auth0.com/authorize"
    token_url = "https://dev-neuromation.auth0.com/oauth/token"
    client_id = "this_is_client_id"
    audience = "https://platform.dev.neuromation.io"
    callback_urls = [
        "http://0.0.0.0:54540",
        "http://0.0.0.0:54541",
        "http://0.0.0.0:54542",
    ]
    success_redirect_url = "https://platform.neuromation.io"
    JSON = {
        "registry_url": registry_url,
        "auth_url": auth_url,
        "token_url": token_url,
        "client_id": client_id,
        "audience": audience,
        "callback_urls": callback_urls,
        "success_redirect_url": success_redirect_url,
    }

    async def handler(request):
        return web.json_response(JSON)

    app = web.Application()
    app.router.add_get("/config", handler)
    srv = await aiohttp_server(app)

    config = await get_server_config(srv.make_url("/"))
    assert config == ServerConfig(
        registry_url=URL(registry_url),
        auth_config=AuthConfig(
            auth_url=URL(auth_url),
            token_url=URL(token_url),
            client_id=client_id,
            audience=audience,
            callback_urls=tuple(URL(u) for u in callback_urls),
            success_redirect_url=URL(success_redirect_url),
        ),
    )


async def test_get_server_config__fail(aiohttp_server):
    async def handler(request):
        raise aiohttp.web.HTTPInternalServerError(reason="unexpected server error")

    app = web.Application()
    app.router.add_get("/config", handler)
    srv = await aiohttp_server(app)

    with pytest.raises(IllegalArgumentError, match="unexpected server error"):
        config = await get_server_config(srv.make_url("/"))
