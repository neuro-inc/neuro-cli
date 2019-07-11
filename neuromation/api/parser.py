from dataclasses import dataclass

from yarl import URL

from .config import _Config
from .parsing_utils import LocalImage, RemoteImage, _ImageNameParser
from .url_utils import normalize_storage_path_uri
from .utils import NoPublicConstructor


@dataclass(frozen=True)
class Volume:
    storage_path: str
    container_path: str
    read_only: bool


class Parser(metaclass=NoPublicConstructor):
    def __init__(self, config: _Config, username: str) -> None:
        self._config = config
        self._username = username

    def volume(self, volume: str) -> Volume:
        parts = volume.split(":")

        read_only = False
        if len(parts) == 4:
            if parts[-1] not in ["ro", "rw"]:
                raise ValueError(f"Wrong ReadWrite/ReadOnly mode spec for '{volume}'")
            read_only = parts.pop() == "ro"
        elif len(parts) != 3:
            raise ValueError(f"Invalid volume specification '{volume}'")

        container_path = parts.pop()
        storage_path = normalize_storage_path_uri(URL(":".join(parts)), self._username)

        return Volume(
            storage_path=str(storage_path),
            container_path=container_path,
            read_only=read_only,
        )

    def local_image(self, image: str) -> LocalImage:
        parser = _ImageNameParser(
            self._config.auth_token.username, self._config.cluster_config.registry_url
        )
        return parser.parse_as_local_image(image)

    def remote_image(self, image: str) -> RemoteImage:
        parser = _ImageNameParser(
            self._config.auth_token.username, self._config.cluster_config.registry_url
        )
        return parser.parse_as_neuro_image(image)
