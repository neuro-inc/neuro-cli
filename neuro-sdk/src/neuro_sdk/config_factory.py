import asyncio
import base64
import json
import os
import ssl
import sys
from pathlib import Path
from typing import Awaitable, Callable, List, Optional

import aiohttp
import certifi
from yarl import URL

from neuro_sdk.login import AuthTokenClient

from .client import Client
from .config import _ConfigData, _load, _load_recovery_data, _save
from .core import DEFAULT_TIMEOUT
from .errors import ConfigError
from .login import AuthNegotiator, HeadlessNegotiator, _AuthToken, logout_from_browser
from .server_cfg import _ServerConfig, get_server_config
from .tracing import _make_trace_config
from .utils import _ContextManager

DEFAULT_CONFIG_PATH = "~/.neuro"
CONFIG_ENV_NAME = "NEUROMATION_CONFIG"
PASS_CONFIG_ENV_NAME = "NEURO_PASSED_CONFIG"
DEFAULT_API_URL = URL("https://staging.neu.ro/api/v1")


def _make_session(
    timeout: aiohttp.ClientTimeout, trace_configs: Optional[List[aiohttp.TraceConfig]]
) -> _ContextManager[aiohttp.ClientSession]:
    return _ContextManager[aiohttp.ClientSession](
        __make_session(timeout, trace_configs)
    )


async def __make_session(
    timeout: aiohttp.ClientTimeout, trace_configs: Optional[List[aiohttp.TraceConfig]]
) -> aiohttp.ClientSession:
    from . import __version__

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    ssl_context.load_verify_locations(capath=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    return aiohttp.ClientSession(
        timeout=timeout,
        connector=connector,
        trace_configs=trace_configs,
        headers={"User-Agent": f"NeuroCLI/{__version__} ({sys.platform})"},
    )


class Factory:
    def __init__(
        self,
        path: Optional[Path] = None,
        trace_configs: Optional[List[aiohttp.TraceConfig]] = None,
        trace_id: Optional[str] = None,
        trace_sampled: Optional[bool] = None,
    ) -> None:
        if path is None:
            path = Path(os.environ.get(CONFIG_ENV_NAME, DEFAULT_CONFIG_PATH))
        self._path = path.expanduser()
        self._trace_configs = [_make_trace_config()]
        if trace_configs:
            self._trace_configs += trace_configs
        self._trace_id = trace_id
        self._trace_sampled = trace_sampled

    @property
    def path(self) -> Path:
        return self._path

    @property
    def is_config_present(self) -> bool:
        return (self._path / "db").exists()

    async def get(self, *, timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT) -> Client:
        if not self.is_config_present and PASS_CONFIG_ENV_NAME in os.environ:
            await self.login_with_passed_config(timeout=timeout)
        try:
            return await self._get(timeout=timeout)
        except ConfigError as initial_error:
            try:
                await self._try_recover_config(timeout)
            except asyncio.CancelledError:
                raise
            except Exception:
                raise initial_error
            return await self._get(timeout=timeout)

    async def _get(self, *, timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT) -> Client:
        session = await _make_session(timeout, self._trace_configs)
        try:
            client = Client._create(
                session, self._path, self._trace_id, self._trace_sampled
            )
            await client.config.check_server()
        except (asyncio.CancelledError, Exception):
            await session.close()
            raise
        else:
            return client

    async def _try_recover_config(
        self, timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT
    ) -> None:
        recovery_data = _load_recovery_data(self._path)
        async with _make_session(timeout, self._trace_configs) as session:
            config_unauthorized = await get_server_config(session, recovery_data.url)
            old_token = _AuthToken.create("", 0, recovery_data.refresh_token)
            async with AuthTokenClient(
                session,
                url=config_unauthorized.auth_config.token_url,
                client_id=config_unauthorized.auth_config.client_id,
            ) as token_client:
                fresh_token = await token_client.refresh(old_token)
            config_authorized = await get_server_config(
                session, recovery_data.url, token=fresh_token.token
            )
            config = self._gen_config(config_authorized, fresh_token, recovery_data.url)
        self._save(config)

        client = await self.get(timeout=timeout)
        await client.config.switch_cluster(recovery_data.cluster_name)
        await client.close()

    async def login(
        self,
        show_browser_cb: Callable[[URL], Awaitable[None]],
        *,
        url: URL = DEFAULT_API_URL,
        timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT,
    ) -> None:
        config_file = self._path / "db"
        if config_file.exists():
            raise ConfigError(f"Config at {self._path} already exists. Please logout")
        async with _make_session(timeout, self._trace_configs) as session:
            config_unauthorized = await get_server_config(session, url)
            negotiator = AuthNegotiator(
                session, config_unauthorized.auth_config, show_browser_cb
            )
            auth_token = await negotiator.get_token()

            config_authorized = await get_server_config(
                session, url, token=auth_token.token
            )
        config = self._gen_config(config_authorized, auth_token, url)
        self._save(config)

    async def login_headless(
        self,
        get_auth_code_cb: Callable[[URL], Awaitable[str]],
        *,
        url: URL = DEFAULT_API_URL,
        timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT,
    ) -> None:
        config_file = self._path / "db"
        if config_file.exists():
            raise ConfigError(f"Config at {self._path} already exists. Please logout")
        async with _make_session(timeout, self._trace_configs) as session:
            config_unauthorized = await get_server_config(session, url)
            negotiator = HeadlessNegotiator(
                session, config_unauthorized.auth_config, get_auth_code_cb
            )
            auth_token = await negotiator.get_token()

            config_authorized = await get_server_config(
                session, url, token=auth_token.token
            )
        config = self._gen_config(config_authorized, auth_token, url)
        self._save(config)

    async def login_with_token(
        self,
        token: str,
        *,
        url: URL = DEFAULT_API_URL,
        timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT,
    ) -> None:
        config_file = self._path / "db"
        if config_file.exists():
            raise ConfigError(f"Config at {self._path} already exists. Please logout")
        async with _make_session(timeout, self._trace_configs) as session:
            server_config = await get_server_config(session, url, token=token)
        config = self._gen_config(
            server_config, _AuthToken.create_non_expiring(token), url
        )
        self._save(config)

    async def login_with_passed_config(
        self,
        config_data: Optional[str] = None,
        *,
        timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT,
    ) -> None:
        if config_data is None:
            try:
                config_data = os.environ[PASS_CONFIG_ENV_NAME]
            except KeyError:
                raise ConfigError(
                    f"Config env variable {PASS_CONFIG_ENV_NAME} " "is not present"
                )
        try:
            data = json.loads(base64.b64decode(config_data).decode())
            token = data["token"]
            cluster = data["cluster"]
            url = URL(data["url"])
        except (ValueError, KeyError):
            raise ConfigError(f"Data in passed config is malformed: {config_data}")
        await self.login_with_token(token, url=url, timeout=timeout)
        client = await self.get(timeout=timeout)

        await client.config.switch_cluster(cluster)
        await client.close()

    def _gen_config(
        self, server_config: _ServerConfig, token: _AuthToken, url: URL
    ) -> _ConfigData:
        from . import __version__

        assert server_config.admin_url, "Authorized config should include admin_url"

        cluster_name = next(iter(server_config.clusters))
        config = _ConfigData(
            auth_config=server_config.auth_config,
            auth_token=token,
            url=url,
            admin_url=server_config.admin_url,
            version=__version__,
            cluster_name=cluster_name,
            clusters=server_config.clusters,
        )
        return config

    async def logout(
        self,
        show_browser_cb: Callable[[URL], Awaitable[None]] = None,
    ) -> None:
        if show_browser_cb is not None:
            try:
                old_config = _load(self._path)
            except ConfigError:
                pass  # Do not try to logout from auth0 if config is broken
            else:
                await logout_from_browser(old_config.auth_config, show_browser_cb)

        files = ["db", "db-wal", "db-shm"]
        for name in files:
            f = self._path / name
            if f.exists():
                f.unlink()
        if self._path.is_file():
            # Old-styled single file config from 2019
            self._path.unlink()
        else:
            try:
                self._path.rmdir()
            except OSError:
                # Directory Not Empty or Not A Directory
                pass

    def _save(self, config: _ConfigData) -> None:
        _save(config, self._path, False)
