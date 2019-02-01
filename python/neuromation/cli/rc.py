import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import aiohttp
import yaml
from yarl import URL

from neuromation.client import Client
from neuromation.client.users import get_token_username
from neuromation.utils import run

from .defaults import API_URL
from .login import AuthConfig, AuthNegotiator, AuthToken


class RCException(Exception):
    pass


def _create_default_auth_config() -> AuthConfig:
    return _create_dev_auth_config()


def _create_dev_auth_config() -> AuthConfig:
    return AuthConfig.create(
        base_url=URL("https://dev-neuromation.auth0.com"),
        client_id="V7Jz87W9lhIlo0MyD0O6dufBvcXwM4DR",
        audience="https://platform.dev.neuromation.io",
        success_redirect_url=URL("https://platform.neuromation.io"),
    )


def _create_staging_auth_config() -> AuthConfig:
    return AuthConfig.create(
        base_url=URL("https://staging-neuromation.auth0.com"),
        client_id="uJV0pm5JPdHkXsSd525rlhFDVcEuUnaV",
        audience="https://platform.staging.neuromation.io",
        success_redirect_url=URL("https://platform.neuromation.io"),
    )


@dataclass
class Config:
    auth_config: AuthConfig = field(default_factory=_create_default_auth_config)
    url: str = API_URL
    auth_token: Optional[AuthToken] = None
    github_rsa_path: str = ""
    color: bool = field(default=False)  # don't save the field in config

    @property
    def auth(self) -> Optional[str]:
        if self.auth_token:
            return self.auth_token.token
        return None

    def docker_registry_url(self) -> URL:
        platform_url = URL(self.url)
        assert platform_url.host
        registry_host = platform_url.host.replace("platform.", "registry.")
        return URL(f"{platform_url.scheme}://{registry_host}")

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
        kwargs = {}
        if timeout is not None:
            kwargs["timeout"] = timeout
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
    def update_api_url(cls, url: str) -> Config:
        cls._validate_api_url(url)
        auth_config = _create_auth_config(URL(url), {})
        return cls._update_config(auth_config=auth_config, url=url)

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
    def refresh_auth_token(cls, url: URL) -> Config:
        nmrc_config_path = cls.get_path()
        config = load(nmrc_config_path)
        cls._validate_api_url(str(url))
        auth_config = _create_auth_config(url, {})
        config = replace(config, auth_config=auth_config, url=str(url), auth_token=None)
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
    success_redirect_url = None
    if config.auth_config.success_redirect_url:
        success_redirect_url = str(config.auth_config.success_redirect_url)

    payload = {
        "url": config.url,
        "auth_config": {
            "auth_url": str(config.auth_config.auth_url),
            "token_url": str(config.auth_config.token_url),
            "client_id": config.auth_config.client_id,
            "audience": config.auth_config.audience,
            "success_redirect_url": success_redirect_url,
        },
        "github_rsa_path": config.github_rsa_path,
    }
    if config.auth_token:
        payload["auth_token"] = {
            "token": config.auth_token.token,
            "expiration_time": config.auth_token.expiration_time,
            "refresh_token": config.auth_token.refresh_token,
        }

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


def _create_auth_token(payload: Dict[str, Any]) -> Optional[AuthToken]:
    if "auth_token" in payload:
        return AuthToken(
            token=payload["auth_token"]["token"],
            expiration_time=payload["auth_token"]["expiration_time"],
            refresh_token=payload["auth_token"]["refresh_token"],
        )
    if "auth" in payload:
        return AuthToken.create_non_expiring(payload["auth"])
    return None


def _create_auth_config(api_url: URL, payload: Dict[str, Any]) -> AuthConfig:
    if "auth_config" in payload:
        success_redirect_url = payload["auth_config"].get("success_redirect_url")
        if success_redirect_url:
            success_redirect_url = URL(success_redirect_url)
        return AuthConfig(
            auth_url=URL(payload["auth_config"]["auth_url"]),
            token_url=URL(payload["auth_config"]["token_url"]),
            client_id=payload["auth_config"]["client_id"],
            audience=payload["auth_config"]["audience"],
            success_redirect_url=success_redirect_url,
        )

    # TODO: temporary hardcoded until /api/v1/config is implemented
    if api_url == URL("https://platform.staging.neuromation.io/api/v1"):
        return _create_staging_auth_config()
    return _create_default_auth_config()


def _load(path: Path) -> Config:
    stat = path.stat()
    if stat.st_mode & 0o777 != 0o600:
        raise RCException(
            f"Config file {path} has compromised permission bits, "
            f"run 'chmod 600 {path}' before usage"
        )
    with path.open("r") as f:
        payload = yaml.load(f)

    api_url = URL(payload["url"])
    auth_config = _create_auth_config(api_url, payload)
    auth_token = _create_auth_token(payload)

    return Config(
        auth_config=auth_config,
        url=str(api_url),
        auth_token=auth_token,
        github_rsa_path=payload.get("github_rsa_path", ""),
    )


def create(path: Path, config: Config) -> Config:
    if Path(path).exists():
        raise FileExistsError(path)

    return save(path, config)
