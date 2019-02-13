import logging
import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import aiohttp
import pkg_resources
import yaml
from yarl import URL

import neuromation
from neuromation.client import Client
from neuromation.client.config import get_server_config
from neuromation.client.users import get_token_username
from neuromation.utils import run

from .defaults import API_URL
from .login import AuthConfig, AuthNegotiator, AuthToken


log = logging.getLogger(__name__)


class RCException(Exception):
    pass


NO_VERSION = pkg_resources.parse_version("0.0.0")


@dataclass
class PyPIVersion:
    pypi_version: Any
    check_timestamp: int

    def warn_if_has_newer_version(self) -> None:
        current = pkg_resources.parse_version(neuromation.__version__)
        if current < self.pypi_version:
            update_command = "pip install --upgrade neuromation"
            log.warning(
                f"You are using Neuromation Platform Client version {current}, "
                f"however version {self.pypi_version} is available. "
            )
            log.warning(
                f"You should consider upgrading via the '{update_command}' command."
            )
            log.warning("")  # tailing endline

    @classmethod
    def from_config(cls, data: Dict[str, Any]) -> "PyPIVersion":
        try:
            pypi_version = pkg_resources.parse_version(data["pypi_version"])
            check_timestamp = int(data["check_timestamp"])
        except (KeyError, TypeError, ValueError):
            # config has invalid/missing data, ignore it
            pypi_version = NO_VERSION
            check_timestamp = 0
        return cls(pypi_version=pypi_version, check_timestamp=check_timestamp)

    def to_config(self) -> Dict[str, Any]:
        return {
            "pypi_version": str(self.pypi_version),
            "check_timestamp": int(self.check_timestamp),
        }


@dataclass
class Config:
    url: str = API_URL
    registry_url: str = ""
    auth_config: AuthConfig = AuthConfig.create_uninitialized()
    auth_token: Optional[AuthToken] = None
    github_rsa_path: str = ""
    pypi: PyPIVersion = field(default_factory=lambda: PyPIVersion(NO_VERSION, 0))
    color: bool = field(default=False)  # don't save the field in config
    tty: bool = field(default=False)  # don't save the field in config
    terminal_size: Tuple[int, int] = field(default=(80, 24))  # don't save it in config

    @property
    def auth(self) -> Optional[str]:
        if self.auth_token:
            return self.auth_token.token
        return None

    def get_platform_user_name(self) -> Optional[str]:
        if self.auth:
            return get_token_username(self.auth)
        return None

    def _check_registered(self) -> Tuple[str, str]:
        auth = self.auth
        if not auth:
            raise RCException("User is not registered, run 'neuro login'.")
        username = get_token_username(auth)
        return auth, username

    @property
    def username(self) -> str:
        # This property intentionally fails for unregistered sessions etc.
        token, username = self._check_registered()
        return username

    def make_client(self, *, timeout: Optional[aiohttp.ClientTimeout] = None) -> Client:
        token, username = self._check_registered()
        kwargs: Dict[str, Any] = {}
        if timeout is not None:
            kwargs["timeout"] = timeout
        if self.registry_url:
            kwargs["registry_url"] = self.registry_url
        return Client(self.url, token, **kwargs)


class ConfigFactory:
    @classmethod
    def get_path(cls) -> Path:
        return Path.home().joinpath(".nmrc")

    @classmethod
    def load(cls) -> Config:
        nmrc_config_path = cls.get_path()
        old_config = load(nmrc_config_path)
        config = cls._refresh_auth_token(old_config)
        if config != old_config:
            save(nmrc_config_path, config)
        return config

    @classmethod
    def update_auth_token(cls, token: str) -> Config:
        get_token_username(token)
        auth_token = AuthToken.create_non_expiring(token)
        return cls._update_config(auth_token=auth_token)

    @classmethod
    def forget_auth_token(cls) -> Config:
        return cls._update_config(auth_token=None)

    @classmethod
    async def update_api_url(cls, url: str) -> Config:
        cls._validate_api_url(url)
        server_config = await get_server_config(URL(url))
        return cls._update_config(
            auth_config=server_config.auth_config,
            registry_url=server_config.registry_url,
            url=url,
        )

    @classmethod
    def _validate_api_url(cls, url: str) -> None:
        if url != "" and url[-1] == "/":
            raise ValueError("URL should not finish with trailing / symbol.")

        parsed_url = URL(url)

        if parsed_url.scheme not in ["http", "https"]:
            raise ValueError("Valid scheme options are http and https.")
        if parsed_url.query_string != "":
            raise ValueError("URL should not contain params.")
        if parsed_url.fragment != "":
            raise ValueError("URL should not contain fragments.")

    @classmethod
    def update_github_rsa_path(cls, github_rsa_path: str) -> Config:
        return cls._update_config(github_rsa_path=github_rsa_path)

    @classmethod
    def update_last_checked_version(cls, version: Any, timestamp: int) -> Config:
        pypi = PyPIVersion(version, timestamp)
        return cls._update_config(pypi=pypi)

    @classmethod
    def refresh_auth_token(cls, url: URL) -> Config:
        nmrc_config_path = cls.get_path()
        config = load(nmrc_config_path)
        cls._validate_api_url(str(url))
        server_config = run(get_server_config(url))
        config = replace(
            config,
            auth_config=server_config.auth_config,
            registry_url=str(server_config.registry_url),
            url=str(url),
            auth_token=None,
        )
        config = cls._refresh_auth_token(config, force=True)
        save(nmrc_config_path, config)
        return config

    @classmethod
    def _refresh_auth_token(cls, config: Config, force: bool = False) -> Config:
        if not config.auth_token and not force:
            return config

        auth_negotiator = AuthNegotiator(config=config.auth_config)
        auth_token = run(auth_negotiator.refresh_token(config.auth_token))
        return replace(config, auth_token=auth_token)

    @classmethod
    def _update_config(cls, **updated_fields: Any) -> Config:
        nmrc_config_path = cls.get_path()
        config = load(nmrc_config_path)
        config = replace(config, **updated_fields)
        return save(nmrc_config_path, config)


def save(path: Path, config: Config) -> Config:
    payload: Dict[str, Any] = {
        "url": config.url,
        "github_rsa_path": config.github_rsa_path,
        "registry_url": config.registry_url,
    }
    if config.auth_config.is_initialized():
        payload["auth_config"] = _serialize_auth_config(config.auth_config)
    if config.auth_token:
        payload["auth_token"] = {
            "token": config.auth_token.token,
            "expiration_time": config.auth_token.expiration_time,
            "refresh_token": config.auth_token.refresh_token,
        }
    payload["pypi"] = config.pypi.to_config()

    # forbid access to other users
    if path.exists():
        # drop a file if exists to reopen it in exclusive mode for writing
        path.unlink()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    with os.fdopen(os.open(path, flags, 0o600), "w") as f:
        yaml.dump(payload, f, default_flow_style=False)
    return config


def load(path: Path) -> Config:
    try:
        return create(path, Config())
    except FileExistsError:
        return _load(path)


def _serialize_auth_config(auth_config: AuthConfig) -> Dict[str, Any]:
    assert auth_config.is_initialized(), auth_config
    success_redirect_url = None
    if auth_config.success_redirect_url:
        success_redirect_url = str(auth_config.success_redirect_url)
    return {
        "auth_url": str(auth_config.auth_url),
        "token_url": str(auth_config.token_url),
        "client_id": auth_config.client_id,
        "audience": auth_config.audience,
        "success_redirect_url": success_redirect_url,
        "callback_urls": [str(u) for u in auth_config.callback_urls],
    }


def _deserialize_auth_config(payload: Dict[str, Any]) -> Optional[AuthConfig]:
    auth_config = payload.get("auth_config")
    if auth_config:
        success_redirect_url = auth_config.get("success_redirect_url")
        if success_redirect_url:
            success_redirect_url = URL(success_redirect_url)
        return AuthConfig(
            auth_url=URL(auth_config["auth_url"]),
            token_url=URL(auth_config["token_url"]),
            client_id=auth_config["client_id"],
            audience=auth_config["audience"],
            success_redirect_url=success_redirect_url,
            callback_urls=tuple(URL(u) for u in auth_config.get("callback_urls", [])),
        )
    return None  # for mypy


def _deserialize_auth_token(payload: Dict[str, Any]) -> Optional[AuthToken]:
    if "auth_token" in payload:
        return AuthToken(
            token=payload["auth_token"]["token"],
            expiration_time=payload["auth_token"]["expiration_time"],
            refresh_token=payload["auth_token"]["refresh_token"],
        )
    if "auth" in payload:
        return AuthToken.create_non_expiring(payload["auth"])
    return None


def _load(path: Path) -> Config:
    stat = path.stat()
    if stat.st_mode & 0o777 != 0o600:
        raise RCException(
            f"Config file {path} has compromised permission bits, "
            f"run 'chmod 600 {path}' before usage"
        )
    with path.open("r") as f:
        payload = yaml.load(f)

    api_url = payload["url"]

    auth_config = _deserialize_auth_config(payload)
    if auth_config is None:
        auth_config = Config.auth_config
    auth_token = _deserialize_auth_token(payload)

    return Config(
        auth_config=auth_config,
        url=api_url,
        # cast to str as somehow yaml.load loads registry_url as 'yaml.URL' not 'str'
        registry_url=str(payload.get("registry_url", "")),
        auth_token=auth_token,
        github_rsa_path=payload.get("github_rsa_path", ""),
        pypi=PyPIVersion.from_config(payload.get("pypi")),
    )


def create(path: Path, config: Config) -> Config:
    if Path(path).exists():
        raise FileExistsError(path)

    return save(path, config)
