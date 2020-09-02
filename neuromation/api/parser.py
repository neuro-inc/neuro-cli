import os
from dataclasses import dataclass
from typing import Dict, Iterator, List, Sequence, Set, Tuple

from yarl import URL

from .config import Config
from .parsing_utils import LocalImage, RemoteImage, TagOption, _ImageNameParser
from .url_utils import normalize_storage_path_uri, uri_from_cli
from .utils import NoPublicConstructor


@dataclass(frozen=True)
class SecretFile:
    secret_uri: URL
    container_path: str


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

    def _build_volumes(self, input_volumes: Set[str]) -> List[Volume]:
        if "HOME" in input_volumes:
            raise ValueError("--volume=HOME no longer supported")
        if "ALL" in input_volumes:
            raise ValueError("--volume=ALL no longer supported")

        return [self.volume(vol) for vol in input_volumes]

    def _build_secret_files(self, input_volumes: Set[str]) -> List[SecretFile]:
        secret_files: List[SecretFile] = []
        for volume in input_volumes:
            parts = volume.split(":")
            if len(parts) != 3:
                raise ValueError(f"Invalid secret file specification '{volume}'")
            container_path = parts.pop()
            secret_uri = self._parse_secret_resource(":".join(parts))
            secret_files.append(SecretFile(secret_uri, container_path))
        return secret_files

    def _parse_secret_resource(self, uri: str) -> URL:
        return uri_from_cli(
            uri,
            self._config.username,
            self._config.cluster_name,
            allowed_schemes=("secret",),
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

    def env(
        self, env: Sequence[str], env_file: Sequence[str] = ()
    ) -> Tuple[Dict[str, str], Dict[str, URL]]:
        env_dict = self._build_env(env, env_file)
        secret_env_dict = self._extract_secret_env(env_dict)
        return env_dict, secret_env_dict

    def _build_env(
        self, env: Sequence[str], env_file: Sequence[str] = ()
    ) -> Dict[str, str]:
        lines: List[str] = []
        for filename in env_file:
            lines.extend(_read_lines(filename))
        lines.extend(env)

        env_dict = {}
        for line in lines:
            splitted = line.split("=", 1)
            name = splitted[0]
            if len(splitted) == 1:
                val = os.environ.get(splitted[0], "")
            else:
                val = splitted[1]
            env_dict[name] = val
        return env_dict

    def _extract_secret_env(self, env_dict: Dict[str, str]) -> Dict[str, URL]:
        secret_env_dict = {}
        for name, val in env_dict.copy().items():
            if val.startswith("secret:"):
                secret_env_dict[name] = self._parse_secret_resource(val)
                del env_dict[name]
        return secret_env_dict

    def volumes(self, volume: Sequence[str]) -> Tuple[List[Volume], List[SecretFile]]:
        input_secret_files = {vol for vol in volume if vol.startswith("secret:")}
        input_volumes = set(volume) - input_secret_files
        secret_files = self._build_secret_files(input_secret_files)
        vols = self._build_volumes(input_volumes)
        return vols, secret_files


def _read_lines(env_file: str) -> Iterator[str]:
    with open(env_file, encoding="utf-8-sig") as ef:
        lines = ef.read().splitlines()
    for line in lines:
        line = line.lstrip()
        if line and not line.startswith("#"):
            yield line
