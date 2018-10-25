from pathlib import Path
from typing import Dict, Optional

import yaml
from dataclasses import asdict, dataclass
from jose import JWTError, jwt
from yarl import URL


@dataclass
class Config:
    url: str = "http://platform.dev.neuromation.io/api/v1"
    auth: str = ""
    github_rsa_path: str = ""

    def docker_registry_url(self) -> str:
        platform_url = URL(self.url)
        docker_registry_url = platform_url.host.replace("platform.", "registry.")
        return docker_registry_url

    def get_platform_user_name(self) -> Optional[str]:
        if self.auth != "" and self.auth is not None:
            jwt_header = jwt.get_unverified_claims(self.auth)
            return jwt_header.get("identity", None)
        return None


class ConfigFactory:
    @classmethod
    def load(cls):
        nmrc_config_path = Path.home().joinpath(".nmrc")
        return load(nmrc_config_path)

    @classmethod
    def update_auth_token(cls, token: str) -> Config:
        try:
            jwt_header = jwt.get_unverified_claims(token)
            if "identity" not in jwt_header:
                raise ValueError("JWT Claims structure is not correct.")
        except JWTError as e:
            raise ValueError(
                f"Passed string does not contain valid JWT structure."
            ) from e

        return cls._update_config(auth=token)

    @classmethod
    def update_api_url(cls, url: str) -> Config:
        return cls._update_config(url=url)

    @classmethod
    def update_github_rsa_path(cls, github_rsa_path: str) -> Config:
        return cls._update_config(github_rsa_path=github_rsa_path)

    @classmethod
    def _update_config(cls, **updated_fields):
        nmrc_config_path = Path.home().joinpath(".nmrc")
        config = load(nmrc_config_path)
        config = cls.merge(config, updated_fields)
        return save(nmrc_config_path, config)

    @classmethod
    def merge(cls, config: Config, kwargs: Dict):
        default = asdict(config)
        for kv in kwargs.items():
            default[kv[0]] = kv[1]
        return Config(**default)


def save(path, config: Config) -> Config:
    with open(path, "w") as file:
        yaml.dump(asdict(config), file, default_flow_style=False)

    return config


def load(path) -> Config:
    try:
        return create(path, Config())
    except FileExistsError:
        with open(path, "r") as file:
            return Config(**yaml.load(file))


def create(path, config):
    if Path(path).exists():
        raise FileExistsError(path)

    return save(path, config)
