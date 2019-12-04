from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

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
class Cluster:
    name: str
    registry_url: URL
    storage_url: URL
    users_url: URL
    monitoring_url: URL
    presets: Mapping[str, Preset]


def _is_cluster_config_initialized(cfg: Cluster) -> bool:
    return bool(
        cfg.registry_url
        and cfg.storage_url
        and cfg.users_url
        and cfg.monitoring_url
        and cfg.presets
    )


@dataclass(frozen=True)
class _ServerConfig:
    auth_config: _AuthConfig
    clusters: Mapping[str, Cluster]


class ConfigLoadException(Exception):
    pass


def _parse_cluster_config(payload: Dict[str, Any]) -> Cluster:
    presets: Dict[str, Preset] = {}
    for data in payload.get("resource_presets", ()):
        tpu_type = tpu_software_version = None
        if "tpu" in data:
            tpu_payload = data.get("tpu")
            tpu_type = tpu_payload["type"]
            tpu_software_version = tpu_payload["software_version"]
        presets[data["name"]] = Preset(
            cpu=data["cpu"],
            memory_mb=data["memory_mb"],
            gpu=data.get("gpu"),
            gpu_model=data.get("gpu_model"),
            is_preemptible=data.get("is_preemptible", False),
            tpu_type=tpu_type,
            tpu_software_version=tpu_software_version,
        )
    cluster_config = Cluster(
        registry_url=URL(payload.get("registry_url", "")),
        storage_url=URL(payload.get("storage_url", "")),
        users_url=URL(payload.get("users_url", "")),
        monitoring_url=URL(payload.get("monitoring_url", "")),
        presets=presets,
        name=payload.get("name", "default"),
    )
    return cluster_config


def _parse_clusters(payload: Dict[str, Any]) -> Dict[str, Cluster]:
    ret: Dict[str, Cluster] = {}
    if "clusters" in payload:
        for item in payload["clusters"]:
            cluster = _parse_cluster_config(item)
            ret[cluster.name] = cluster
    else:
        # old server without multiple clusters support
        cluster = _parse_cluster_config(payload)
        if _is_cluster_config_initialized(cluster):
            ret[cluster.name] = cluster
    return ret


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
        clusters = _parse_clusters(payload)
        if headers and not clusters:
            raise AuthException("Cannot authorize user")
        return _ServerConfig(auth_config=auth_config, clusters=clusters)
