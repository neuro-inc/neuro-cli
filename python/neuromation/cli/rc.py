from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from yarl import URL

from neuromation.clientv2.users import get_token_username


class RCException(Exception):
    pass


@dataclass
class Config:
    url: str = "https://platform.dev.neuromation.io/api/v1"
    auth: Optional[str] = None
    github_rsa_path: str = ""

    def docker_registry_url(self) -> URL:
        platform_url = URL(self.url)
        assert platform_url.host
        registry_host = platform_url.host.replace("platform.", "registry.")
        return URL(f"{platform_url.scheme}://{registry_host}")

    def get_platform_user_name(self) -> Optional[str]:
        if self.auth != "" and self.auth is not None:
            return get_token_username(self.auth)
        return None


class ConfigFactory:
    @classmethod
    def load(cls) -> Config:
        nmrc_config_path = Path.home().joinpath(".nmrc")
        return load(nmrc_config_path)

    @classmethod
    def update_auth_token(cls, token: str) -> Config:
        get_token_username(token)
        return cls._update_config(auth=token)

    @classmethod
    def forget_auth_token(cls) -> Config:
        return cls._update_config(auth=None)

    @classmethod
    def update_api_url(cls, url: str) -> Config:
        if url != "" and url[-1] == "/":
            raise ValueError("URL should not finish with trailing / symbol.")

        parsed_url = URL(url)

        if parsed_url.scheme not in ["http", "https"]:
            raise ValueError("Valid scheme options are http and https.")
        if parsed_url.query_string != "":
            raise ValueError("URL should not contain params.")
        if parsed_url.fragment != "":
            raise ValueError("URL should not contain fragments.")

        return cls._update_config(url=url)

    @classmethod
    def update_github_rsa_path(cls, github_rsa_path: str) -> Config:
        return cls._update_config(github_rsa_path=github_rsa_path)

    @classmethod
    def _update_config(cls, **updated_fields: Any) -> Config:
        nmrc_config_path = Path.home().joinpath(".nmrc")
        config = load(nmrc_config_path)
        config = cls.merge(config, updated_fields)
        return save(nmrc_config_path, config)

    @classmethod
    def merge(cls, config: Config, kwargs: Dict[str, Any]) -> Config:
        default = asdict(config)
        for kv in kwargs.items():
            default[kv[0]] = kv[1]
        return Config(**default)


def save(path: Path, config: Config) -> Config:
    payload = asdict(config)

    with open(path, "w") as f:
        yaml.dump(payload, f, default_flow_style=False)

    return config


def load(path: Path) -> Config:
    try:
        return create(path, Config())
    except FileExistsError:
        return _load(path)


def _load(path: Path) -> Config:
    with open(path, "r") as f:
        payload = yaml.load(f)

    return Config(
        url=payload["url"],
        auth=payload.get("auth"),
        github_rsa_path=payload.get("github_rsa_path", ""),
    )


def create(path: Path, config: Config) -> Config:
    if Path(path).exists():
        raise FileExistsError(path)

    return save(path, config)
