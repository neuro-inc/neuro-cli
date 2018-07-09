from pathlib import Path

import yaml
from dataclasses import asdict, dataclass


@dataclass
class Config:
    url: str = 'http://platform.dev.neuromation.io/api/v1'


def _save(path, config: Config) -> Config:
    with open(path, 'w') as file:
        yaml.dump(asdict(config), file, default_flow_style=False)

    return config


def load(path):
    try:
        return create(path)
    except FileExistsError:
        with open(path, 'r') as file:
            return Config(**yaml.load(file))


def create(path):
    if (Path(path).exists()):
        raise FileExistsError(path)

    return _save(path, Config())
