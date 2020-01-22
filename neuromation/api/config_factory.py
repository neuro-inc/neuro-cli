import asyncio
import os
import sqlite3
import ssl
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import aiohttp
import certifi
import yaml
from yarl import URL

import neuromation

from .client import Client
from .config import (
    MALFORMED_CONFIG_MSG,
    Config,
    ConfigError,
    _check_db,
    _Config,
    _CookieSession,
    _PyPIVersion,
)
from .core import DEFAULT_TIMEOUT
from .login import (
    AuthNegotiator,
    HeadlessNegotiator,
    _AuthConfig,
    _AuthToken,
    refresh_token,
)
from .server_cfg import Cluster, Preset, _ServerConfig, get_server_config
from .tracing import _make_trace_config
from .utils import _ContextManager


WIN32 = sys.platform == "win32"
DEFAULT_CONFIG_PATH = "~/.neuro"
CONFIG_ENV_NAME = "NEUROMATION_CONFIG"
TRUSTED_CONFIG_PATH = "NEUROMATION_TRUSTED_CONFIG_PATH"
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
        timeout=timeout, connector=connector, trace_configs=trace_configs
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

    async def get(self, *, timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT) -> Client:
        saved_config = config = self._read()
        session = await _make_session(timeout, self._trace_configs)
        try:
            new_token = await refresh_token(
                session, config.auth_config, config.auth_token
            )
            if config.version != neuromation.__version__:
                config_authorized = await get_server_config(
                    session, config.url, token=new_token.token
                )
                if (
                    config_authorized.clusters != config.clusters
                    or config_authorized.auth_config != config.auth_config
                ):
                    raise ConfigError(
                        "Neuro Platform CLI updated. Please logout and login again."
                    )
                config = replace(config, version=neuromation.__version__)
            if new_token != config.auth_token:
                config = replace(config, auth_token=new_token)
            if config != saved_config:
                # _save() may raise malformed config exception
                # Should close connector in this case
                self._save(config)
        except (asyncio.CancelledError, Exception):
            await session.close()
            raise
        else:
            return Client._create(session, config, self._path, self._trace_id)

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
            auth_token = await negotiator.refresh_token()

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
            auth_token = await negotiator.refresh_token()

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
    ) -> _Config:
        cluster_name = next(iter(server_config.clusters))
        config = _Config(
            auth_config=server_config.auth_config,
            auth_token=token,
            pypi=_PyPIVersion.create_uninitialized(),
            url=url,
            cookie_session=_CookieSession.create_uninitialized(),
            version=neuromation.__version__,
            cluster_name=cluster_name,
            clusters=server_config.clusters,
        )
        return config

    async def logout(self) -> None:
        # TODO: logout from auth0
        config_file = self._path / "db"
        if config_file.exists():
            config_file.unlink()
        if self._path.is_file():
            self._path.unlink()
        else:
            try:
                self._path.rmdir()
            except OSError:
                # Directory Not Empty or Not A Directory
                pass

    def _read(self) -> _Config:
        config_file = self._path / "db"
        if not self._path.exists():
            raise ConfigError(f"Config at {self._path} does not exists. Please login.")
        if not self._path.is_dir():
            raise ConfigError(
                f"Config at {self._path} is not a directory. "
                "Please logout and login again."
            )
        if not config_file.is_file():
            raise ConfigError(
                f"Config {config_file} is not a regular file. "
                "Please logout and login again."
            )

        trusted_env = WIN32 or bool(os.environ.get(TRUSTED_CONFIG_PATH))
        if not trusted_env:
            stat_dir = self._path.stat()
            if stat_dir.st_mode & 0o777 != 0o700:
                raise ConfigError(
                    f"Config {self._path} has compromised permission bits, "
                    f"run 'chmod 700 {self._path}' first"
                )
            stat_file = config_file.stat()
            if stat_file.st_mode & 0o777 != 0o600:
                raise ConfigError(
                    f"Config at {config_file} has compromised permission bits, "
                    f"run 'chmod 600 {config_file}' first"
                )

        try:
            with sqlite3.connect(str(config_file)) as db:
                _check_db(db)

                cur = db.cursor()
                cur.execute("SELECT content FROM main ORDER BY ROWID ASC LIMIT 1")
                content = cur.fetchone()[0]

            payload = yaml.safe_load(content)

            api_url = URL(payload["url"])
            pypi_payload = payload["pypi"]
            auth_config = self._deserialize_auth_config(payload)
            clusters = self._deserialize_clusters(payload)
            auth_token = self._deserialize_auth_token(payload)
            cookie_session = _CookieSession.from_config(
                payload.get("cookie_session", {})
            )
            version = payload.get("version", "")
            cluster_name = payload["cluster_name"]

            return _Config(
                auth_config=auth_config,
                auth_token=auth_token,
                pypi=_PyPIVersion.from_config(pypi_payload),
                url=api_url,
                cookie_session=cookie_session,
                version=version,
                cluster_name=cluster_name,
                clusters=clusters,
            )
        except (AttributeError, KeyError, TypeError, ValueError, sqlite3.DatabaseError):
            raise ConfigError(MALFORMED_CONFIG_MSG)

    def _deserialize_auth_config(self, payload: Dict[str, Any]) -> _AuthConfig:
        auth_config = payload["auth_config"]
        success_redirect_url = auth_config.get("success_redirect_url")
        if success_redirect_url:
            success_redirect_url = URL(success_redirect_url)
        return _AuthConfig(
            auth_url=URL(auth_config["auth_url"]),
            token_url=URL(auth_config["token_url"]),
            client_id=auth_config["client_id"],
            audience=auth_config["audience"],
            headless_callback_url=URL(auth_config["headless_callback_url"]),
            success_redirect_url=success_redirect_url,
            callback_urls=tuple(URL(u) for u in auth_config.get("callback_urls", [])),
        )

    def _deserialize_clusters(self, payload: Dict[str, Any]) -> Dict[str, Cluster]:
        clusters = payload["clusters"]
        ret: Dict[str, Cluster] = {}
        for cluster_config in clusters:
            cluster = Cluster(
                name=cluster_config["name"],
                registry_url=URL(cluster_config["registry_url"]),
                storage_url=URL(cluster_config["storage_url"]),
                users_url=URL(cluster_config["users_url"]),
                monitoring_url=URL(cluster_config["monitoring_url"]),
                presets=dict(
                    self._deserialize_resource_preset(data)
                    for data in cluster_config.get("presets", [])
                ),
            )
            ret[cluster.name] = cluster
        return ret

    def _deserialize_resource_preset(
        self, payload: Dict[str, Any]
    ) -> Tuple[str, Preset]:
        return (
            payload["name"],
            Preset(
                cpu=payload["cpu"],
                memory_mb=payload["memory_mb"],
                gpu=payload.get("gpu"),
                gpu_model=payload.get("gpu_model"),
                tpu_type=payload.get("tpu_type", None),
                tpu_software_version=payload.get("tpu_software_version", None),
                is_preemptible=payload.get("is_preemptible", False),
            ),
        )

    def _deserialize_auth_token(self, payload: Dict[str, Any]) -> _AuthToken:
        auth_payload = payload["auth_token"]
        return _AuthToken(
            token=auth_payload["token"],
            expiration_time=auth_payload["expiration_time"],
            refresh_token=auth_payload["refresh_token"],
        )

    def _save(self, config: _Config) -> None:
        # Trampoline to Config._save() method
        # Looks ugly a little, fix me later.
        Config._save(config, self._path)
