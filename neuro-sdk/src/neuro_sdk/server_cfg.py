from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Mapping, Optional

import aiohttp
from yarl import URL

from .errors import AuthError
from .login import _AuthConfig


@dataclass(frozen=True)
class Preset:
    credits_per_hour: Decimal
    cpu: float
    memory_mb: int
    scheduler_enabled: bool = False
    preemptible_node: bool = False
    gpu: Optional[int] = None
    gpu_model: Optional[str] = None
    tpu_type: Optional[str] = None
    tpu_software_version: Optional[str] = None


@dataclass(frozen=True)
class Cluster:
    name: str
    registry_url: URL
    storage_url: URL
    blob_storage_url: URL
    users_url: URL
    monitoring_url: URL
    secrets_url: URL
    disks_url: URL
    presets: Mapping[str, Preset]


@dataclass(frozen=True)
class _ServerConfig:
    admin_url: Optional[URL]
    auth_config: _AuthConfig
    clusters: Mapping[str, Cluster]


def _parse_cluster_config(payload: Dict[str, Any]) -> Cluster:
    presets: Dict[str, Preset] = {}
    for data in payload["resource_presets"]:
        tpu_type = tpu_software_version = None
        if "tpu" in data:
            tpu_payload = data["tpu"]
            tpu_type = tpu_payload["type"]
            tpu_software_version = tpu_payload["software_version"]
        presets[data["name"]] = Preset(
            # TODO: make credits_per_hour not optional after server updated
            credits_per_hour=Decimal(data.get("credits_per_hour", "0")),
            cpu=data["cpu"],
            memory_mb=data["memory_mb"],
            gpu=data.get("gpu"),
            gpu_model=data.get("gpu_model"),
            scheduler_enabled=data.get("scheduler_enabled", False),
            preemptible_node=data.get("preemptible_node", False),
            tpu_type=tpu_type,
            tpu_software_version=tpu_software_version,
        )
    cluster_config = Cluster(
        name=payload["name"],
        registry_url=URL(payload["registry_url"]),
        storage_url=URL(payload["storage_url"]),
        blob_storage_url=URL(payload["blob_storage_url"]),
        users_url=URL(payload["users_url"]),
        monitoring_url=URL(payload["monitoring_url"]),
        secrets_url=URL(payload["secrets_url"]),
        disks_url=URL(payload["disks_url"]),
        presets=presets,
    )
    return cluster_config


def _parse_clusters(payload: Dict[str, Any]) -> Dict[str, Cluster]:
    ret: Dict[str, Cluster] = {}
    for item in payload.get("clusters", {}):
        cluster = _parse_cluster_config(item)
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
            logout_url=URL(payload["logout_url"]),
            client_id=payload["client_id"],
            audience=payload["audience"],
            success_redirect_url=success_redirect_url,
            callback_urls=callback_urls,
            headless_callback_url=headless_callback_url,
        )
        clusters = _parse_clusters(payload)
        admin_url: Optional[URL] = None
        if "admin_url" in payload:
            admin_url = URL(payload["admin_url"])
        if headers and (not clusters or not admin_url):
            raise AuthError("Cannot authorize user")
        return _ServerConfig(
            admin_url=admin_url,
            auth_config=auth_config,
            clusters=clusters,
        )
