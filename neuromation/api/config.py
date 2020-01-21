import base64
import contextlib
import numbers
import os
import re
import sqlite3
import time
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Iterator, List, Mapping, Set, Union

import dateutil.parser
import pkg_resources
import toml
import yaml
from yarl import URL

from .core import _Core
from .login import _AuthConfig, _AuthToken
from .server_cfg import Cluster, Preset, get_server_config
from .utils import NoPublicConstructor


class ConfigError(RuntimeError):
    pass


CMD_RE = re.compile("[A-Za-z][A-Za-z0-9-]*")

MALFORMED_CONFIG_MSG = "Malformed config. Please logout and login again."


SCHEMA = {"main": "CREATE TABLE main (content TEXT, timestamp REAL)"}


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
    clusters: Mapping[str, Cluster]


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
        return MappingProxyType(cluster.presets)

    @property
    def clusters(self) -> Mapping[str, Cluster]:
        return MappingProxyType(self._config_data.clusters)

    @property
    def cluster_name(self) -> str:
        name = self._config_data.cluster_name
        return name

    async def fetch(self) -> None:
        server_config = await get_server_config(
            self._core._session,
            self._config_data.url,
            self._config_data.auth_token.token,
        )
        if self.cluster_name not in server_config.clusters:
            # Raise exception here?
            # if yes there is not way to switch cluster without relogin
            raise RuntimeError(
                f"Cluster {self.cluster_name} doesn't exist in "
                f"a list of available clusters "
                f"{list(server_config.clusters)}. "
                f"Please logout and login again."
            )
        self._config_data = replace(self._config_data, clusters=server_config.clusters)
        self._save(self._config_data, self._path)

    async def switch_cluster(self, name: str) -> None:
        if name not in self.clusters:
            raise RuntimeError(
                f"Cluster {name} doesn't exist in "
                f"a list of available clusters {list(self.clusters)}. "
                f"Please logout and login again."
            )
        self._config_data = replace(self._config_data, cluster_name=name)
        self._save(self._config_data, self._path)

    @property
    def api_url(self) -> URL:
        return self._config_data.url

    @property
    def admin_url(self) -> URL:
        # XXX: Replace the path to match all APIs or do discovery

        # API URL prefix: api/v1, admin prefix: apis/admin/v1
        return self._config_data.url.parent.parent / "apis" / "admin" / "v1"

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

    async def token(self) -> str:
        # TODO: refresh token here if needed
        return self._config_data.auth_token.token

    async def _api_auth(self) -> str:
        token = await self.token()
        return f"Bearer {token}"

    async def _docker_auth(self) -> Dict[str, str]:
        token = await self.token()
        return {"username": "token", "password": token}

    async def _registry_auth(self) -> str:
        token = await self.token()
        return "Basic " + base64.b64encode(
            f"{self.username}:{token}".encode("ascii")
        ).decode("ascii")

    async def get_user_config(self) -> Mapping[str, Any]:
        # TODO: search in several locations (HOME+curdir),
        # merge found configs
        filename = self._path / "user.toml"
        if not filename.exists():
            # Empty global configuration
            config: Mapping[str, Any] = {}
        elif not filename.is_file():
            raise ConfigError(f"User config {filename} should be a regular file")
        else:
            config = _load_file(filename)
        folder = Path.cwd()
        while True:
            filename = folder / ".neuro.toml"
            if filename.exists() and filename.is_file():
                local_config = _load_file(filename)
                return _merge_user_configs(config, local_config)
            if folder == folder.parent:
                # No local config is found
                return config
            else:
                folder = folder.parent

    @contextlib.contextmanager
    def _open_db(self) -> Iterator[sqlite3.Connection]:
        config_file = self._path / "db"
        with sqlite3.connect(str(config_file)) as db:
            db.row_factory = sqlite3.Row
            yield db
            db.commit()

    @classmethod
    def _save(cls, config: _Config, path: Path) -> None:
        # The wierd method signature is required for communicating with existing
        # Factory._save()
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
            raise ConfigError(MALFORMED_CONFIG_MSG)

        path.mkdir(0o700, parents=True, exist_ok=True)

        config_file = path / "db"
        with sqlite3.connect(str(config_file)) as db:
            # forbid access to other users
            os.chmod(config_file, 0o600)

            _init_db_maybe(db)

            cur = db.cursor()
            content = yaml.safe_dump(payload, default_flow_style=False)
            cur.execute("DELETE FROM main")
            cur.execute(
                """
                INSERT INTO main (content, timestamp)
                VALUES (?, ?)""",
                (content, time.time()),
            )
            db.commit()

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
        cls, clusters: Mapping[str, Cluster]
    ) -> List[Dict[str, Any]]:
        ret: List[Dict[str, Any]] = []
        for cluster in clusters.values():
            cluster_config = {
                "name": cluster.name,
                "registry_url": str(cluster.registry_url),
                "storage_url": str(cluster.storage_url),
                "users_url": str(cluster.users_url),
                "monitoring_url": str(cluster.monitoring_url),
                "presets": [
                    cls._serialize_resource_preset(name, preset)
                    for name, preset in cluster.presets.items()
                ],
            }
            ret.append(cluster_config)
        return ret

    @classmethod
    def _serialize_resource_preset(cls, name: str, preset: Preset) -> Dict[str, Any]:
        return {
            "name": name,
            "cpu": preset.cpu,
            "memory_mb": preset.memory_mb,
            "gpu": preset.gpu,
            "gpu_model": preset.gpu_model,
            "tpu_type": preset.tpu_type,
            "tpu_software_version": preset.tpu_software_version,
            "is_preemptible": preset.is_preemptible,
        }


def _merge_user_configs(
    older: Mapping[str, Any], newer: Mapping[str, Any]
) -> Mapping[str, Any]:
    ret: Dict[str, Any] = {}
    for key, val in older.items():
        if key not in newer:
            # keep older key/values
            ret[key] = val
        else:
            # key is present in both newer and older
            new_val = newer[key]
            if isinstance(new_val, Mapping) and isinstance(val, Mapping):
                # merge nested dictionaries
                ret[key] = _merge_user_configs(val, new_val)
            else:
                # for non-dicts newer overrides older
                ret[key] = new_val
    for key in newer.keys() - older.keys():
        # Add keys/values from newer that absent in older
        ret[key] = newer[key]
    return ret


def _check_sections(
    config: Mapping[str, Any],
    valid_names: Set[str],
    filename: Union[str, "os.PathLike[str]"],
) -> None:
    extra_sections = config.keys() - valid_names
    if extra_sections:
        raise ConfigError(
            f"{filename}: unsupported config sections: {extra_sections!r}"
        )
    for name in valid_names:
        section = config.get(name, {})
        if not isinstance(section, dict):
            raise ConfigError(
                f"{filename}: {name!r} should be a section, got {section!r}"
            )


def _check_item(
    val: Any, validator: Any, full_name: str, filename: Union[str, "os.PathLike[str]"],
) -> None:
    if isinstance(validator, tuple):
        container_type, item_type = validator
        if not isinstance(val, container_type):
            raise ConfigError(
                f"{filename}: invalid type for {full_name}, "
                f"{container_type.__name__} is expected"
            )
        for num, i in enumerate(val):
            _check_item(i, item_type, f"{full_name}[{num}]", filename)
    else:
        assert isinstance(validator, type) and issubclass(
            validator, (bool, numbers.Real, numbers.Integral, str)
        )
        # validator for integer types should be numbers.Real or numbers.Integral,
        # not int or float
        if not isinstance(val, validator):
            raise ConfigError(
                f"{filename}: invalid type for {full_name}, "
                f"{validator.__name__} is expected"
            )


def _check_section(
    config: Mapping[str, Any],
    section: str,
    params: Dict[str, Any],
    filename: Union[str, "os.PathLike[str]"],
) -> None:
    sec = config.get(section)
    if sec is None:
        return
    diff = sec.keys() - params.keys()
    if diff:
        diff_str = ", ".join(f"{section}.{name}" for name in sorted(diff))
        raise ConfigError(f"{filename}: unknown parameters {diff_str}")
    for name, validator in params.items():
        val = sec.get(name)
        if val is None:
            continue
        _check_item(val, validator, f"{section}.{name}", filename)


def _validate_user_config(
    config: Mapping[str, Any], filename: Union[str, "os.PathLike[str]"]
) -> None:
    # This was a hard decision.
    # Config structure should be validated to generate meaningful error messages.
    #
    # API should do it but API don't use user config itself, the config is entirely
    # for CLI needs.
    #
    # Since currently CLI is the only API client that reads user config data, API
    # validates it.
    #
    # Later, after possible introduction of plugin subsystem the validation should
    # be extended by plugin-provided rules.  That will be done by providing
    # additional API for describing new supported config sections, keys and values.
    # Right now this functionality is skipped for the sake of simplicity.
    _check_sections(config, {"alias", "job", "storage"}, filename)
    _check_section(config, "job", {"ps-format": str}, filename)
    _check_section(config, "storage", {"cp-exclude": (list, str)}, filename)
    aliases = config.get("alias", {})
    for key, value in aliases.items():
        # check keys and values
        if not CMD_RE.fullmatch(key):
            raise ConfigError(f"{filename}: invalid alias name {key}")
        if not isinstance(value, str):
            raise ConfigError(
                f"{filename}: invalid alias command type {type(value)}, "
                "a string is expected"
            )


def _load_file(filename: Path) -> Mapping[str, Any]:
    config = toml.load(filename)
    _validate_user_config(config, filename)
    return config


def _load_schema(db: sqlite3.Connection) -> Dict[str, str]:
    cur = db.cursor()
    schema = {}
    cur.execute("SELECT type, name, sql from sqlite_master")
    for type, name, sql in cur:
        if type not in ("table", "index"):
            continue
        if name.startswith("sqlite"):
            # internal object
            continue
        schema[name] = sql
    return schema


def _check_db(db: sqlite3.Connection) -> None:
    schema = _load_schema(db)
    for name, sql in SCHEMA.items():
        if name not in schema:
            raise ConfigError(MALFORMED_CONFIG_MSG)
        if sql != schema[name]:
            raise ConfigError(MALFORMED_CONFIG_MSG)


def _init_db_maybe(db: sqlite3.Connection) -> None:
    # create schema for empty database if needed
    schema = _load_schema(db)
    cur = db.cursor()
    for name, sql in SCHEMA.items():
        if name not in schema:
            cur.execute(sql)
