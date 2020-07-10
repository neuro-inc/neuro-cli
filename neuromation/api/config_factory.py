import asyncio
import os
import ssl
import sys
from pathlib import Path
from typing import Awaitable, Callable, List, Optional

import aiohttp
import certifi
from yarl import URL

import neuromation

from .client import Client
from .config import ConfigError, _ConfigData, _save
from .core import DEFAULT_TIMEOUT
from .login import AuthNegotiator, HeadlessNegotiator, _AuthToken
from .server_cfg import _ServerConfig, get_server_config
from .tracing import _make_trace_config
from .utils import _ContextManager


DEFAULT_CONFIG_PATH = "~/.neuro"
CONFIG_ENV_NAME = "NEUROMATION_CONFIG"
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
    ssl_context = ssl.SSLContext()
    ssl_context.load_verify_locations(capath=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    return aiohttp.ClientSession(
        timeout=timeout,
        connector=connector,
        trace_configs=trace_configs,
        headers={"User-Agent": f"NeuroCLI/{neuromation.__version__} ({sys.platform})"},
    )


class Factory:
    def __init__(
        self,
        path: Optional[Path] = None,
        trace_configs: Optional[List[aiohttp.TraceConfig]] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        if path is None:
            path = Path(os.environ.get(CONFIG_ENV_NAME, DEFAULT_CONFIG_PATH))
        self._path = path.expanduser()
        self._trace_configs = [_make_trace_config()]
        if trace_configs:
            self._trace_configs += trace_configs
        self._trace_id = trace_id

    @property
    def path(self) -> Path:
        return self._path

    async def get(self, *, timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT) -> Client:
        session = await _make_session(timeout, self._trace_configs)
        try:
            client = Client._create(session, self._path, self._trace_id)
            await client.config.check_server()
        except (asyncio.CancelledError, Exception):
            await session.close()
            raise
        else:
            return client

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

    def _gen_config(
        self, server_config: _ServerConfig, token: _AuthToken, url: URL
    ) -> _ConfigData:
        cluster_name = next(iter(server_config.clusters))
        config = _ConfigData(
            auth_config=server_config.auth_config,
            auth_token=token,
            url=url,
            version=neuromation.__version__,
            cluster_name=cluster_name,
            clusters=server_config.clusters,
        )
        return config

    async def logout(self) -> None:
        # TODO: logout from auth0
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
        _save(config, self._path)
