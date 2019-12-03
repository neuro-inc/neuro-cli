import base64
from dataclasses import dataclass, replace
from datetime import date
from types import MappingProxyType
from typing import Any, Dict, Mapping

import dateutil.parser
import pkg_resources
from yarl import URL

from .core import _Core
from .login import _AuthConfig, _AuthToken
from .server_cfg import ClusterConfig, Preset, get_server_config
from .utils import NoPublicConstructor


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
    def __init__(self, core: _Core, config_data: _Config) -> None:
        self._core = core
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
        # TODO: raise an error if the current cluster doesn't exist
        self._config_data = replace(self._config_data, clusters=server_config.clusters)

    async def switch_cluster(self, name: str) -> None:
        pass

    def _save(self) -> None:
        pass

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
