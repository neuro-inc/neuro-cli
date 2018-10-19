from pathlib import Path
from typing import Optional

import yaml
from dataclasses import asdict, dataclass
from jose import jwt
from yarl import URL


@dataclass
class Config:
    url: str = 'http://platform.dev.neuromation.io/api/v1'
    auth: str = ''
    github_rsa_path: str = ''

    def docker_registry_url(self) -> str:
        platform_url = URL(self.url)
        docker_registry_url = platform_url.\
            host.replace('platform.', 'registry.')
        return docker_registry_url

    def get_platform_user_name(self) -> Optional[str]:
        if self.auth != '' and self.auth is not None:
            jwt_header = jwt.get_unverified_claims(self.auth)
            return jwt_header.get('identity', None)
        return None


class ConfigFactory:
    @classmethod
    def load(cls):
        nmrc_config_path = Path.home().joinpath('.nmrc')
        return load(nmrc_config_path)

    @classmethod
    def save(cls, config: Config):
        nmrc_config_path = Path.home().joinpath('.nmrc')
        return save(nmrc_config_path, config)


def save(path, config: Config) -> Config:
    with open(path, 'w') as file:
        yaml.dump(asdict(config), file, default_flow_style=False)

    return config


def load(path) -> Config:
    try:
        return create(path, Config())
    except FileExistsError:
        with open(path, 'r') as file:
            return Config(**yaml.load(file))


def create(path, config):
    if Path(path).exists():
        raise FileExistsError(path)

    return save(path, config)
