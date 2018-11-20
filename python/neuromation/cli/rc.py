from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Optional

import keyring
import yaml
from jose import JWTError, jwt
from yarl import URL


@dataclass
class Config:
    url: str = "http://platform.dev.neuromation.io/api/v1"
    auth: str = None
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


CREDENTIAL_FIELDS = ["auth"]
CREDENTIAL_SERVICE_NAME = "neuro"


def save(path, config: Config) -> Config:
    dict_config = asdict(config)
    for field in CREDENTIAL_FIELDS:
        value = dict_config.pop(field, None)
        if value is None:
            try:
                keyring.delete_password(CREDENTIAL_SERVICE_NAME, field)
            except Exception:
                pass
        else:
            try:
                keyring.set_password(CREDENTIAL_SERVICE_NAME, field, value)
            except Exception:
                if value is not None:
                    dict_config[field] = value

    with open(path, "w") as file:
        yaml.dump(dict_config, file, default_flow_style=False)

    return config


def load(path) -> Config:
    try:
        return create(path, Config())
    except FileExistsError:
        with open(path, "r") as file:
            dict_config = yaml.load(file)
            for field in CREDENTIAL_FIELDS:
                # Legacy fields from plain file will be supported too,
                # it`s usable for tests
                value = dict_config.get(field, None)
                if value is None:
                    try:
                        value = keyring.get_password(CREDENTIAL_SERVICE_NAME, field)
                        dict_config[field] = value
                    except Exception:  # pragma: no cover
                        pass  # pragma: no cover
            return Config(**dict_config)


def create(path, config):
    if Path(path).exists():
        raise FileExistsError(path)

    return save(path, config)
