from dataclasses import dataclass

from yarl import URL

from .config import Config
from .parsing_utils import LocalImage, RemoteImage, TagOption, _ImageNameParser
from .url_utils import normalize_storage_path_uri
from .utils import NoPublicConstructor


@dataclass(frozen=True)
class Volume:
    storage_uri: URL
    container_path: str
    read_only: bool = False


class Parser(metaclass=NoPublicConstructor):
    def __init__(self, config: Config) -> None:
        self._config = config

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
        storage_uri = normalize_storage_path_uri(
            URL(":".join(parts)), self._config.username, self._config.cluster_name
        )

        return Volume(
            storage_uri=storage_uri, container_path=container_path, read_only=read_only
        )

    def local_image(self, image: str) -> LocalImage:
        parser = _ImageNameParser(
            self._config.username, self._config.cluster_name, self._config.registry_url
        )
        return parser.parse_as_local_image(image)

    def remote_image(
        self, image: str, *, tag_option: TagOption = TagOption.DEFAULT
    ) -> RemoteImage:
        parser = _ImageNameParser(
            self._config.username, self._config.cluster_name, self._config.registry_url
        )
        return parser.parse_remote(image, tag_option=tag_option)

    def _local_to_remote_image(self, image: LocalImage) -> RemoteImage:
        parser = _ImageNameParser(
            self._config.username, self._config.cluster_name, self._config.registry_url
        )
        return parser.convert_to_neuro_image(image)

    def _remote_to_local_image(self, image: RemoteImage) -> LocalImage:
        parser = _ImageNameParser(
            self._config.username, self._config.cluster_name, self._config.registry_url
        )
        return parser.convert_to_local_image(image)
