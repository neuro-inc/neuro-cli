import base64
import contextlib
import json
import numbers
import os
import re
import sqlite3
import sys
import time
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Iterator, List, Mapping, Optional, Set, Tuple, Union

import toml
from yarl import URL

import neuromation

from .core import _Core
from .login import AuthTokenClient, _AuthConfig, _AuthToken
from .server_cfg import Cluster, Preset, _ServerConfig, get_server_config
from .utils import NoPublicConstructor, flat


class ConfigError(RuntimeError):
    pass


WIN32 = sys.platform == "win32"
CMD_RE = re.compile("[A-Za-z][A-Za-z0-9-]*")

MALFORMED_CONFIG_MSG = "Malformed config. Please logout and login again."


SCHEMA = {
    "main": flat(
        """
        CREATE TABLE main (auth_config TEXT,
                           token TEXT,
                           expiration_time REAL,
                           refresh_token TEXT,
                           url TEXT,
                           version TEXT,
                           cluster_name TEXT,
                           clusters TEXT,
                           timestamp REAL)"""
    )
}


@dataclass(frozen=True)
class _ConfigData:
    auth_config: _AuthConfig
    auth_token: _AuthToken
    url: URL
    version: str
    cluster_name: str
    clusters: Mapping[str, Cluster]


class Config(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, path: Path) -> None:
        self._core = core
        self._path = path
        self.__config_data: Optional[_ConfigData] = None

    def _load(self) -> _ConfigData:
        ret = self.__config_data = _load(self._path)
        return ret

    @property
    def _config_data(self) -> _ConfigData:
        ret = self.__config_data
        if ret is None:
            return self._load()
        else:
            return ret

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

    async def _fetch_config(self) -> _ServerConfig:
        token = await self.token()
        return await get_server_config(self._core._session, self.api_url, token)

    async def check_server(self) -> None:
        if self._config_data.version != neuromation.__version__:
            config_authorized = await self._fetch_config()
            if (
                config_authorized.clusters != self.clusters
                or config_authorized.auth_config != self._config_data.auth_config
            ):
                raise ConfigError(
                    "Neuro Platform CLI was updated. Please logout and login again."
                )
            self.__config_data = replace(
                self._config_data, version=neuromation.__version__
            )
            _save(self._config_data, self._path)

    async def fetch(self) -> None:
        server_config = await self._fetch_config()
        if self.cluster_name not in server_config.clusters:
            # Raise exception here?
            # if yes there is not way to switch cluster without relogin
            raise RuntimeError(
                f"Cluster {self.cluster_name} doesn't exist in "
                f"a list of available clusters "
                f"{list(server_config.clusters)}. "
                f"Please logout and login again."
            )
        self.__config_data = replace(self._config_data, clusters=server_config.clusters)
        _save(self._config_data, self._path)

    async def switch_cluster(self, name: str) -> None:
        if name not in self.clusters:
            raise RuntimeError(
                f"Cluster {name} doesn't exist in "
                f"a list of available clusters {list(self.clusters)}. "
                f"Please logout and login again."
            )
        self.__config_data = replace(self._config_data, cluster_name=name)
        _save(self._config_data, self._path)

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
    def blob_storage_url(self) -> URL:
        cluster = self._config_data.clusters[self._config_data.cluster_name]
        # XXX: Updata properly the API to return Object storage as separate URL
        return URL(str(cluster.storage_url).replace("/storage", "/blob"))

    @property
    def storage_url(self) -> URL:
        cluster = self._config_data.clusters[self._config_data.cluster_name]
        return cluster.storage_url

    @property
    def registry_url(self) -> URL:
        cluster = self._config_data.clusters[self._config_data.cluster_name]
        return cluster.registry_url

    async def token(self) -> str:
        token = self._config_data.auth_token
        if not token.is_expired():
            return token.token
        async with AuthTokenClient(
            self._core._session,
            url=self._config_data.auth_config.token_url,
            client_id=self._config_data.auth_config.client_id,
        ) as token_client:
            new_token = await token_client.refresh(token)
            self.__config_data = replace(self._config_data, auth_token=new_token)
            with self._open_db() as db:
                _save_auth_token(db, new_token)
            return new_token.token

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
        with _open_db_rw(self._path) as db:
            yield db


@contextlib.contextmanager
def _open_db_rw(path: Path) -> Iterator[sqlite3.Connection]:
    path.mkdir(0o700, parents=True, exist_ok=True)

    config_file = path / "db"
    with sqlite3.connect(str(config_file)) as db:
        # forbid access to other users
        os.chmod(config_file, 0o600)

        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        yield db


@contextlib.contextmanager
def _open_db_ro(path: Path) -> Iterator[sqlite3.Connection]:
    config_file = path / "db"
    if not path.exists():
        raise ConfigError(f"Config at {path} does not exists. Please login.")
    if not path.is_dir():
        raise ConfigError(
            f"Config at {path} is not a directory. Please logout and login again."
        )
    if not config_file.is_file():
        raise ConfigError(
            f"Config {config_file} is not a regular file. "
            "Please logout and login again."
        )

    if not WIN32:
        stat_dir = path.stat()
        if stat_dir.st_mode & 0o777 != 0o700:
            raise ConfigError(
                f"Config {path} has compromised permission bits, "
                f"run 'chmod 700 {path}' first"
            )
        stat_file = config_file.stat()
        if stat_file.st_mode & 0o777 != 0o600:
            raise ConfigError(
                f"Config at {config_file} has compromised permission bits, "
                f"run 'chmod 600 {config_file}' first"
            )

    with sqlite3.connect(str(config_file)) as db:
        # forbid access to other users
        os.chmod(config_file, 0o600)

        _check_db(db)
        db.row_factory = sqlite3.Row
        yield db


def _load(path: Path) -> _ConfigData:
    try:
        with _open_db_ro(path) as db:
            cur = db.cursor()
            # only one row is always present normally
            cur.execute(
                """
                SELECT auth_config, token, expiration_time, refresh_token,
                       url, version, cluster_name, clusters
                FROM main ORDER BY timestamp DESC LIMIT 1"""
            )
            payload = cur.fetchone()

        api_url = URL(payload["url"])
        auth_config = _deserialize_auth_config(payload)
        clusters = _deserialize_clusters(payload)
        version = payload["version"]
        cluster_name = payload["cluster_name"]

        auth_token = _AuthToken(
            payload["token"], payload["expiration_time"], payload["refresh_token"]
        )

        return _ConfigData(
            auth_config=auth_config,
            auth_token=auth_token,
            url=api_url,
            version=version,
            cluster_name=cluster_name,
            clusters=clusters,
        )
    except (AttributeError, KeyError, TypeError, ValueError, sqlite3.DatabaseError):
        raise ConfigError(MALFORMED_CONFIG_MSG)


def _deserialize_auth_config(payload: Dict[str, Any]) -> _AuthConfig:
    auth_config = json.loads(payload["auth_config"])
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


def _deserialize_clusters(payload: Dict[str, Any]) -> Dict[str, Cluster]:
    clusters = json.loads(payload["clusters"])
    ret: Dict[str, Cluster] = {}
    for cluster_config in clusters:
        cluster = Cluster(
            name=cluster_config["name"],
            registry_url=URL(cluster_config["registry_url"]),
            storage_url=URL(cluster_config["storage_url"]),
            users_url=URL(cluster_config["users_url"]),
            monitoring_url=URL(cluster_config["monitoring_url"]),
            presets=dict(
                _deserialize_resource_preset(data)
                for data in cluster_config.get("presets", [])
            ),
        )
        ret[cluster.name] = cluster
    return ret


def _deserialize_resource_preset(payload: Dict[str, Any]) -> Tuple[str, Preset]:
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


def _deserialize_auth_token(payload: Dict[str, Any]) -> _AuthToken:
    auth_payload = payload["auth_token"]
    return _AuthToken(
        token=auth_payload["token"],
        expiration_time=auth_payload["expiration_time"],
        refresh_token=auth_payload["refresh_token"],
    )


def _save_auth_token(db: sqlite3.Connection, token: _AuthToken) -> None:
    db.execute(
        "UPDATE main SET token=?, expiration_time=?, refresh_token=?",
        (token.token, token.expiration_time, token.refresh_token),
    )
    with contextlib.suppress(sqlite3.OperationalError):
        db.commit()


def _save(config: _ConfigData, path: Path) -> None:
    # The wierd method signature is required for communicating with existing
    # Factory._save()
    try:
        url = str(config.url)
        auth_config = _serialize_auth_config(config.auth_config)
        clusters = _serialize_clusters(config.clusters)
        version = config.version
        cluster_name = config.cluster_name
        token = config.auth_token
    except (AttributeError, KeyError, TypeError, ValueError):
        raise ConfigError(MALFORMED_CONFIG_MSG)

    with _open_db_rw(path) as db:
        _init_db_maybe(db)

        cur = db.cursor()
        cur.execute("DELETE FROM main")
        cur.execute(
            """
            INSERT INTO main
            (auth_config, token, expiration_time, refresh_token,
             url, version, cluster_name, clusters, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                auth_config,
                token.token,
                token.expiration_time,
                token.refresh_token,
                url,
                version,
                cluster_name,
                clusters,
                time.time(),
            ),
        )
        db.commit()


def _serialize_auth_config(auth_config: _AuthConfig) -> str:
    success_redirect_url = None
    if auth_config.success_redirect_url:
        success_redirect_url = str(auth_config.success_redirect_url)
    return json.dumps(
        {
            "auth_url": str(auth_config.auth_url),
            "token_url": str(auth_config.token_url),
            "client_id": auth_config.client_id,
            "audience": auth_config.audience,
            "headless_callback_url": str(auth_config.headless_callback_url),
            "success_redirect_url": success_redirect_url,
            "callback_urls": [str(u) for u in auth_config.callback_urls],
        }
    )


def _serialize_clusters(clusters: Mapping[str, Cluster]) -> str:
    ret: List[Dict[str, Any]] = []
    for cluster in clusters.values():
        cluster_config = {
            "name": cluster.name,
            "registry_url": str(cluster.registry_url),
            "storage_url": str(cluster.storage_url),
            "users_url": str(cluster.users_url),
            "monitoring_url": str(cluster.monitoring_url),
            "presets": [
                _serialize_resource_preset(name, preset)
                for name, preset in cluster.presets.items()
            ],
        }
        ret.append(cluster_config)
    return json.dumps(ret)


def _serialize_resource_preset(name: str, preset: Preset) -> Dict[str, Any]:
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
    _check_section(
        config, "job", {"ps-format": str, "life-span": str}, filename,
    )
    _check_section(config, "storage", {"cp-exclude": (list, str)}, filename)
    aliases = config.get("alias", {})
    for key, value in aliases.items():
        # check keys and values
        if not CMD_RE.fullmatch(key):
            raise ConfigError(f"{filename}: invalid alias name {key}")
        if not isinstance(value, dict):
            raise ConfigError(
                f"{filename}: invalid alias command type {type(value)}, "
                "'run neuro help aliases' for getting info about specifying "
                "aliases in config files"
            )
        _validate_alias(key, value, filename)


def _validate_alias(
    key: str, value: Dict[str, str], filename: Union[str, "os.PathLike[str]"]
) -> None:
    # TODO: add validation for both internal and external aliases
    pass


def _load_file(filename: Path) -> Mapping[str, Any]:
    try:
        config = toml.load(filename)
    except ValueError as exc:
        raise ConfigError(f"{filename}: {exc}")
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
