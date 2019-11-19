import asyncio
import os
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
from .config import _Config, _CookieSession, _PyPIVersion
from .core import DEFAULT_TIMEOUT
from .login import (
    AuthNegotiator,
    HeadlessNegotiator,
    Preset,
    _AuthConfig,
    _AuthToken,
    _ClusterConfig,
    get_server_config,
    refresh_token,
)
from .tracing import _make_trace_config
from .utils import _ContextManager


WIN32 = sys.platform == "win32"
DEFAULT_CONFIG_PATH = "~/.nmrc"
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


class ConfigError(RuntimeError):
    pass


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
                    config_authorized.cluster_config != config.cluster_config
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
            return Client._create(session, config, self._trace_id)

    async def login(
        self,
        show_browser_cb: Callable[[URL], Awaitable[None]],
        *,
        url: URL = DEFAULT_API_URL,
        timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT,
    ) -> None:
        if self._path.exists():
            raise ConfigError(f"Config file {self._path} already exists. Please logout")
        async with _make_session(timeout, self._trace_configs) as session:
            config_unauthorized = await get_server_config(session, url)
            negotiator = AuthNegotiator(
                session, config_unauthorized.auth_config, show_browser_cb
            )
            auth_token = await negotiator.refresh_token()

            config_authorized = await get_server_config(
                session, url, token=auth_token.token
            )
        config = _Config(
            auth_config=config_authorized.auth_config,
            auth_token=auth_token,
            cluster_config=config_authorized.cluster_config,
            pypi=_PyPIVersion.create_uninitialized(),
            url=url,
            cookie_session=_CookieSession.create_uninitialized(),
            version=neuromation.__version__,
        )
        self._save(config)

    async def login_headless(
        self,
        get_auth_code_cb: Callable[[URL], Awaitable[str]],
        *,
        url: URL = DEFAULT_API_URL,
        timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT,
    ) -> None:
        if self._path.exists():
            raise ConfigError(f"Config file {self._path} already exists. Please logout")
        async with _make_session(timeout, self._trace_configs) as session:
            config_unauthorized = await get_server_config(session, url)
            negotiator = HeadlessNegotiator(
                session, config_unauthorized.auth_config, get_auth_code_cb
            )
            auth_token = await negotiator.refresh_token()

            config_authorized = await get_server_config(
                session, url, token=auth_token.token
            )
        config = _Config(
            auth_config=config_authorized.auth_config,
            auth_token=auth_token,
            cluster_config=config_authorized.cluster_config,
            pypi=_PyPIVersion.create_uninitialized(),
            url=url,
            cookie_session=_CookieSession.create_uninitialized(),
            version=neuromation.__version__,
        )
        self._save(config)

    async def login_with_token(
        self,
        token: str,
        *,
        url: URL = DEFAULT_API_URL,
        timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT,
    ) -> None:
        if self._path.exists():
            raise ConfigError(f"Config file {self._path} already exists. Please logout")
        async with _make_session(timeout, self._trace_configs) as session:
            server_config = await get_server_config(session, url, token=token)
        config = _Config(
            auth_config=server_config.auth_config,
            auth_token=_AuthToken.create_non_expiring(token),
            cluster_config=server_config.cluster_config,
            pypi=_PyPIVersion.create_uninitialized(),
            url=url,
            cookie_session=_CookieSession.create_uninitialized(),
            version=neuromation.__version__,
        )
        self._save(config)

    async def logout(self) -> None:
        # TODO: logout from auth0
        if self._path.exists():
            self._path.unlink()

    def _read(self) -> _Config:
        if not self._path.exists():
            raise ConfigError(f"Config file {self._path} does not exists. Please login")
        if not self._path.is_file():
            raise ConfigError(f"Config {self._path} is not a regular file")

        trusted_env = WIN32 or bool(os.environ.get(TRUSTED_CONFIG_PATH))
        if not trusted_env:
            stat = self._path.stat()
            if stat.st_mode & 0o777 != 0o600:
                raise ConfigError(
                    f"Config file {self._path} has compromised permission bits, "
                    f"run 'chmod 600 {self._path}' first"
                )
        with self._path.open("r", encoding="utf-8") as f:
            payload = yaml.safe_load(f)

        try:
            api_url = URL(payload["url"])
            pypi_payload = payload["pypi"]
            auth_config = self._deserialize_auth_config(payload)
            cluster_config = self._deserialize_cluster_config(payload)
            auth_token = self._deserialize_auth_token(payload)
            cookie_session = _CookieSession.from_config(
                payload.get("cookie_session", {})
            )
            version = payload.get("version", "")

            return _Config(
                auth_config=auth_config,
                cluster_config=cluster_config,
                auth_token=auth_token,
                pypi=_PyPIVersion.from_config(pypi_payload),
                url=api_url,
                cookie_session=cookie_session,
                version=version,
            )
        except (AttributeError, KeyError, TypeError, ValueError):
            raise ConfigError("Malformed config. Please logout and login again.")

    def _serialize_auth_config(self, auth_config: _AuthConfig) -> Dict[str, Any]:
        if not auth_config.is_initialized():
            raise ValueError("auth config part is not initialized")
        success_redirect_url = None
        if auth_config.success_redirect_url:
            success_redirect_url = str(auth_config.success_redirect_url)
        return {
            "auth_url": str(auth_config.auth_url),
            "token_url": str(auth_config.token_url),
            "client_id": auth_config.client_id,
            "audience": auth_config.audience,
            "headless_callback_url": str(auth_config.headless_callback_url),
            "success_redirect_url": success_redirect_url,
            "callback_urls": [str(u) for u in auth_config.callback_urls],
        }

    def _serialize_cluster_config(
        self, cluster_config: _ClusterConfig
    ) -> Dict[str, Any]:
        if not cluster_config.is_initialized():
            raise ValueError("cluster config part is not initialized")
        return {
            "registry_url": str(cluster_config.registry_url),
            "storage_url": str(cluster_config.storage_url),
            "users_url": str(cluster_config.users_url),
            "monitoring_url": str(cluster_config.monitoring_url),
            "resource_presets": [
                self._serialize_resource_preset(name, resource_preset)
                for name, resource_preset in cluster_config.resource_presets.items()
            ],
        }

    def _serialize_resource_preset(
        self, name: str, resource_preset: Preset
    ) -> Dict[str, Any]:
        return {
            "name": name,
            "cpu": resource_preset.cpu,
            "memory_mb": resource_preset.memory_mb,
            "gpu": resource_preset.gpu,
            "gpu_model": resource_preset.gpu_model,
            "tpu_type": resource_preset.tpu_type,
            "tpu_software_version": resource_preset.tpu_software_version,
            "is_preemptible": resource_preset.is_preemptible,
        }

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

    def _deserialize_cluster_config(self, payload: Dict[str, Any]) -> _ClusterConfig:
        cluster_config = payload["cluster_config"]
        return _ClusterConfig.create(
            registry_url=URL(cluster_config["registry_url"]),
            storage_url=URL(cluster_config["storage_url"]),
            users_url=URL(cluster_config["users_url"]),
            monitoring_url=URL(cluster_config["monitoring_url"]),
            resource_presets=dict(
                self._deserialize_resource_preset(data)
                for data in cluster_config.get("resource_presets", [])
            ),
        )

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
        payload: Dict[str, Any] = {}
        try:
            payload["url"] = str(config.url)
            payload["auth_config"] = self._serialize_auth_config(config.auth_config)
            payload["cluster_config"] = self._serialize_cluster_config(
                config.cluster_config
            )
            payload["auth_token"] = {
                "token": config.auth_token.token,
                "expiration_time": config.auth_token.expiration_time,
                "refresh_token": config.auth_token.refresh_token,
            }
            payload["pypi"] = config.pypi.to_config()
            payload["cookie_session"] = config.cookie_session.to_config()
            payload["version"] = config.version
        except (AttributeError, KeyError, TypeError, ValueError):
            raise ConfigError("Malformed config. Please logout and login again.")

        # atomically rewrite the config file
        tmppath = f"{self._path}.new{os.getpid()}"
        try:
            # forbid access to other users
            def opener(file: str, flags: int) -> int:
                return os.open(file, flags, 0o600)

            with open(tmppath, "x", encoding="utf-8", opener=opener) as f:
                yaml.safe_dump(payload, f, default_flow_style=False)
            os.replace(tmppath, self._path)
        except:  # noqa  # bare 'except' with 'raise' is legal
            try:
                os.unlink(tmppath)
            except FileNotFoundError:
                pass
            raise
