import base64
import os
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, List, Mapping

import dateutil.parser
import pkg_resources
import yaml
from yarl import URL

from .core import _Core
from .login import _AuthConfig, _AuthToken
from .server_cfg import ClusterConfig, Preset, get_server_config
from .utils import NoPublicConstructor


class ConfigError(RuntimeError):
    pass


@dataclass
class _PyPIVersion:
    NO_VERSION = pkg_resources.parse_version("0.0.0")

    pypi_version: Any
    check_timestamp: int
    certifi_pypi_version: Any
    certifi_check_timestamp: int
    certifi_pypi_upload_date: date = date.min

    @classmethod
    def create_uninitialized(cls) -> "_PyPIVersion":
        return cls(cls.NO_VERSION, 0, cls.NO_VERSION, 0, date.min)

    @classmethod
    def from_config(cls, data: Dict[str, Any]) -> "_PyPIVersion":
        try:
            pypi_version = pkg_resources.parse_version(data["pypi_version"])
            check_timestamp = int(data["check_timestamp"])
        except (KeyError, TypeError, ValueError):
            # config has invalid/missing data, ignore it
            pypi_version = cls.NO_VERSION
            check_timestamp = 0
        try:
            certifi_pypi_version = pkg_resources.parse_version(
                data["certifi_pypi_version"]
            )
            upload_time_str = data.get("certifi_pypi_upload_date")
            certifi_pypi_upload_date = (
                cls._deserialize_date(upload_time_str) if upload_time_str else date.min
            )
            certifi_check_timestamp = int(data["certifi_check_timestamp"])
        except (KeyError, TypeError, ValueError):
            # config has invalid/missing data, ignore it
            certifi_pypi_version = cls.NO_VERSION
            certifi_check_timestamp = 0
            certifi_pypi_upload_date = date.min
        return cls(
            pypi_version=pypi_version,
            check_timestamp=check_timestamp,
            certifi_pypi_version=certifi_pypi_version,
            certifi_pypi_upload_date=certifi_pypi_upload_date,
            certifi_check_timestamp=certifi_check_timestamp,
        )

    def to_config(self) -> Dict[str, Any]:
        ret = {
            "pypi_version": str(self.pypi_version),
            "check_timestamp": int(self.check_timestamp),
            "certifi_pypi_version": str(self.certifi_pypi_version),
            "certifi_check_timestamp": self.certifi_check_timestamp,
        }
        if self.certifi_pypi_upload_date != date.min:
            value = self._serialize_date(self.certifi_pypi_upload_date)
            ret["certifi_pypi_upload_date"] = value

        return ret

    @classmethod
    def _deserialize_date(cls, value: str) -> date:
        # from format: "2019-08-19"
        return dateutil.parser.parse(value).date()

    @classmethod
    def _serialize_date(cls, value: date) -> str:
        # to format: "2019-08-19"
        return value.strftime("%Y-%m-%d")


@dataclass(frozen=True)
class _CookieSession:
    cookie: str
    timestamp: int

    @classmethod
    def create_uninitialized(cls) -> "_CookieSession":
        return cls(cookie="", timestamp=0)

    @classmethod
    def from_config(cls, data: Dict[str, Any]) -> "_CookieSession":
        cookie = data.get("cookie", "")
        timestamp = data.get("timestamp", 0)
        return cls(cookie=cookie, timestamp=timestamp)

    def to_config(self) -> Dict[str, Any]:
        return {"cookie": self.cookie, "timestamp": self.timestamp}


@dataclass(frozen=True)
class _Config:
    auth_config: _AuthConfig
    auth_token: _AuthToken
    pypi: _PyPIVersion
    url: URL
    cookie_session: _CookieSession
    version: str
    cluster_name: str
    clusters: Mapping[str, ClusterConfig]


class Config(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, path: Path, config_data: _Config) -> None:
        self._core = core
        self._path = path
        self._config_data = config_data

    @property
    def username(self) -> str:
        return self._config_data.auth_token.username

    @property
    def presets(self) -> Mapping[str, Preset]:
        cluster = self._config_data.clusters[self._config_data.cluster_name]
        return MappingProxyType(cluster.resource_presets)

    @property
    def clusters(self) -> Mapping[str, ClusterConfig]:
        return MappingProxyType(self._config_data.clusters)

    @property
    def cluster_name(self) -> str:
        # During the transition period,
        # clusters and cluster.name can be None
        name = self._config_data.cluster_name
        return name

    async def fetch(self) -> None:
        server_config = await get_server_config(
            self._core._session,
            self._config_data.url,
            self._config_data.auth_token.token,
        )
        if self.cluster_name not in server_config.clusters:
            raise RuntimeError(
                f"Cluster {self.cluster_name} doesn't exist in "
                f"a list of available clusters "
                f"{list(server_config.clusters)}"
            )
        self._config_data = replace(self._config_data, clusters=server_config.clusters)

    async def switch_cluster(self, name: str) -> None:
        if name not in self.clusters:
            raise RuntimeError(
                f"Cluster {name} doesn't exist in "
                f"a list of available clusters {list(self.clusters)}"
            )
        self._config_data = replace(self._config_data, cluster_name=name)
        self._save(self._config_data, self._path)

    @property
    def api_url(self) -> URL:
        return self._config_data.url

    @property
    def monitoring_url(self) -> URL:
        cluster = self._config_data.clusters[self._config_data.cluster_name]
        return cluster.monitoring_url

    @property
    def storage_url(self) -> URL:
        cluster = self._config_data.clusters[self._config_data.cluster_name]
        return cluster.storage_url

    @property
    def registry_url(self) -> URL:
        cluster = self._config_data.clusters[self._config_data.cluster_name]
        return cluster.registry_url

    @property
    def token(self) -> str:
        return self._config_data.auth_token.token

    @property
    def _api_auth(self) -> str:
        return f"Bearer {self.token}"

    @property
    def _docker_auth(self) -> Dict[str, str]:
        return {"username": "token", "password": self.token}

    @property
    def _registry_auth(self) -> str:
        return "Basic " + base64.b64encode(
            f"{self.username}:{self.token}".encode("ascii")
        ).decode("ascii")

    @classmethod
    def _save(cls, config: _Config, path: Path) -> None:
        payload: Dict[str, Any] = {}
        try:
            payload["url"] = str(config.url)
            payload["auth_config"] = cls._serialize_auth_config(config.auth_config)
            payload["clusters"] = cls._serialize_clusters(config.clusters)
            payload["auth_token"] = {
                "token": config.auth_token.token,
                "expiration_time": config.auth_token.expiration_time,
                "refresh_token": config.auth_token.refresh_token,
            }
            payload["pypi"] = config.pypi.to_config()
            payload["cookie_session"] = config.cookie_session.to_config()
            payload["version"] = config.version
            payload["cluster_name"] = config.cluster_name
        except (AttributeError, KeyError, TypeError, ValueError):
            raise ConfigError("Malformed config. Please logout and login again.")

        # atomically rewrite the config file
        tmppath = f"{path}.new{os.getpid()}"
        try:
            # forbid access to other users
            def opener(file: str, flags: int) -> int:
                return os.open(file, flags, 0o600)

            path.mkdir(0o700, parents=True, exist_ok=True)
            with open(tmppath, "x", encoding="utf-8", opener=opener) as f:
                yaml.safe_dump(payload, f, default_flow_style=False)
            os.replace(tmppath, path / "db")
        except:  # noqa  # bare 'except' with 'raise' is legal
            try:
                os.unlink(tmppath)
            except FileNotFoundError:
                pass
            raise

    @classmethod
    def _serialize_auth_config(cls, auth_config: _AuthConfig) -> Dict[str, Any]:
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

    @classmethod
    def _serialize_clusters(
        cls, clusters: Mapping[str, ClusterConfig]
    ) -> List[Dict[str, Any]]:
        ret: List[Dict[str, Any]] = []
        for cluster in clusters.values():
            cluster_config = {
                "name": cluster.name,
                "registry_url": str(cluster.registry_url),
                "storage_url": str(cluster.storage_url),
                "users_url": str(cluster.users_url),
                "monitoring_url": str(cluster.monitoring_url),
                "resource_presets": [
                    cls._serialize_resource_preset(name, resource_preset)
                    for name, resource_preset in cluster.resource_presets.items()
                ],
            }
            ret.append(cluster_config)
        return ret

    @classmethod
    def _serialize_resource_preset(
        cls, name: str, resource_preset: Preset
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
