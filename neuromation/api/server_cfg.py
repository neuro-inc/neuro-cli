from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import aiohttp
from yarl import URL

from .login import AuthException, _AuthConfig


@dataclass(frozen=True)
class Preset:
    cpu: float
    memory_mb: int
    is_preemptible: bool = False
    gpu: Optional[int] = None
    gpu_model: Optional[str] = None
    tpu_type: Optional[str] = None
    tpu_software_version: Optional[str] = None


@dataclass(frozen=True)
class _ClusterConfig:
    registry_url: URL
    storage_url: URL
    users_url: URL
    monitoring_url: URL
    resource_presets: Dict[str, Preset]
    name: Optional[str]  # can be None for backward compatibility

    @classmethod
    def create(
        cls,
        registry_url: URL,
        storage_url: URL,
        users_url: URL,
        monitoring_url: URL,
        resource_presets: Dict[str, Preset],
        name: Optional[str] = None,
    ) -> "_ClusterConfig":
        return cls(
            registry_url,
            storage_url,
            users_url,
            monitoring_url,
            resource_presets,
            name=name,
        )

    def is_initialized(self) -> bool:
        return bool(
            self.registry_url
            and self.storage_url
            and self.users_url
            and self.monitoring_url
            and self.resource_presets
        )


@dataclass(frozen=True)
class _ServerConfig:
    auth_config: _AuthConfig
    # the field exists for the transition period at least
    cluster_config: _ClusterConfig
    # clusters are not stored in config file
    # they are exits for fetching from API and displaying by CLI commands
    # Later we maybe change it.
    clusters: List[_ClusterConfig] = field(default_factory=list)


class ConfigLoadException(Exception):
    pass


def _parse_cluster_config(payload: Dict[str, Any]) -> _ClusterConfig:
    resource_presets: Dict[str, Preset] = {}
    for data in payload.get("resource_presets", ()):
        tpu_type = tpu_software_version = None
        if "tpu" in data:
            tpu_payload = data.get("tpu")
            tpu_type = tpu_payload["type"]
            tpu_software_version = tpu_payload["software_version"]
        resource_presets[data["name"]] = Preset(
            cpu=data["cpu"],
            memory_mb=data["memory_mb"],
            gpu=data.get("gpu"),
            gpu_model=data.get("gpu_model"),
            is_preemptible=data.get("is_preemptible", False),
            tpu_type=tpu_type,
            tpu_software_version=tpu_software_version,
        )
    cluster_config = _ClusterConfig(
        registry_url=URL(payload.get("registry_url", "")),
        storage_url=URL(payload.get("storage_url", "")),
        users_url=URL(payload.get("users_url", "")),
        monitoring_url=URL(payload.get("monitoring_url", "")),
        resource_presets=resource_presets,
        name=payload.get("name"),
    )
    return cluster_config


async def get_server_config(
    client: aiohttp.ClientSession, url: URL, token: Optional[str] = None
) -> _ServerConfig:
    headers: Dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with client.get(url / "config", headers=headers) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Unable to get server configuration: {resp.status}")
        payload = await resp.json()
        # TODO (ajuszkowski, 5-Feb-2019) validate received data
        success_redirect_url = URL(payload.get("success_redirect_url", "")) or None
        callback_urls = payload.get("callback_urls")
        callback_urls = (
            tuple(URL(u) for u in callback_urls)
            if callback_urls is not None
            else _AuthConfig.callback_urls
        )
        headless_callback_url = URL(payload["headless_callback_url"])
        auth_config = _AuthConfig(
            auth_url=URL(payload["auth_url"]),
            token_url=URL(payload["token_url"]),
            client_id=payload["client_id"],
            audience=payload["audience"],
            success_redirect_url=success_redirect_url,
            callback_urls=callback_urls,
            headless_callback_url=headless_callback_url,
        )
        cluster_config = _parse_cluster_config(payload)
        clusters = [_parse_cluster_config(item) for item in payload.get("clusters", [])]
        if headers and not cluster_config.is_initialized():
            raise AuthException("Cannot authorize user")
        return _ServerConfig(
            cluster_config=cluster_config, auth_config=auth_config, clusters=clusters
        )
