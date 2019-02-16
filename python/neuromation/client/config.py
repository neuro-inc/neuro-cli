from dataclasses import dataclass

import aiohttp
from yarl import URL

from neuromation.cli.login import AuthConfig
from neuromation.client import DEFAULT_TIMEOUT
from neuromation.client.users import get_token_username


@dataclass(frozen=True)
class ServerConfig:
    auth_config: AuthConfig
    registry_url: URL


class Config:
    def __init__(self, url: URL, registry_url: URL, token: str) -> None:
        self._url = url
        self._registry_url = registry_url
        assert token, "Empty token is not allowed"
        self._token = token
        self._username = get_token_username(token)

    @property
    def url(self) -> URL:
        return self._url

    @property
    def registry_url(self) -> URL:
        return self._registry_url

    @property
    def token(self) -> str:
        return self._token

    @property
    def username(self) -> str:
        return self._username


class ConfigLoadException(Exception):
    pass


async def get_server_config(url: URL) -> ServerConfig:
    async with aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT) as client:
        async with client.get(url / "config") as resp:
            if resp.status != 200:
                raise RuntimeError(f"Unable to get server configuration: {resp.status}")
            payload = await resp.json()
            # TODO (ajuszkowski, 5-Feb-2019) validate received data
            auth_url = URL(payload["auth_url"])
            token_url = URL(payload["token_url"])
            client_id = payload["client_id"]
            audience = payload["audience"]
            success_redirect_url = payload.get("success_redirect_url")
            if success_redirect_url is not None:
                success_redirect_url = URL(success_redirect_url)
            callback_urls = payload.get("callback_urls")
            callback_urls = (
                tuple(URL(u) for u in callback_urls)
                if callback_urls is not None
                else AuthConfig.callback_urls
            )
            auth_config = AuthConfig(
                auth_url=auth_url,
                token_url=token_url,
                client_id=client_id,
                audience=audience,
                success_redirect_url=success_redirect_url,
                callback_urls=callback_urls,
            )
            registry_url = URL(payload["registry_url"])
            return ServerConfig(registry_url=registry_url, auth_config=auth_config)
