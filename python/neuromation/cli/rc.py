from pathlib import Path

import yaml
from dataclasses import asdict, dataclass
from yarl import URL


@dataclass
class Config:
    url: str = 'http://platform.dev.neuromation.io/api/v1'
    auth: str = ''

    def docker_registry_url(self) -> str:
        platform_url = URL(self.url)
        docker_registry_url = platform_url.\
            host.replace('platform.', 'registry.')
        return docker_registry_url


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
