import os
import warnings
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Sequence, Set, Tuple, overload

from typing_extensions import Literal
from yarl import URL

from .config import Config
from .parsing_utils import LocalImage, RemoteImage, TagOption, _ImageNameParser
from .url_utils import uri_from_cli
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


@dataclass(frozen=True)
class DiskVolume:
    disk_uri: URL
    container_path: str
    read_only: bool = False


@dataclass(frozen=True)
class VolumeParseResult:
    volumes: Sequence[Volume]
    secret_files: Sequence[SecretFile]
    disk_volumes: Sequence[DiskVolume]

    # backward compatibility

    def __len__(self) -> int:
        warnings.warn(
            "tuple-like access to client.parse.volumes() result is deprecated "
            "and scheduled for removal in future Neuro CLI release. "
            "Please access by attribute names) instead, "
            "e.g. client.parse.volumes().secret_files",
            DeprecationWarning,
            stacklevel=2,
        )
        return 2

    @overload
    def __getitem__(self, idx: Literal[0]) -> Sequence[Volume]:
        pass

    @overload
    def __getitem__(self, idx: Literal[1]) -> Sequence[SecretFile]:
        pass

    def __getitem__(self, idx: Any) -> Any:
        warnings.warn(
            "tuple-like access to client.parse.volumes() result is deprecated "
            "and scheduled for removal in future Neuro CLI release. "
            "Please access by attribute names) instead, "
            "e.g. client.parse.volumes().secret_files",
            DeprecationWarning,
            stacklevel=2,
        )
        if idx == 0:
            return self.volumes
        elif idx == 1:
            return self.secret_files
        else:
            raise IndexError(idx)


@dataclass(frozen=True)
class EnvParseResult:
    env: Dict[str, str]
    secret_env: Dict[str, URL]


class Parser(metaclass=NoPublicConstructor):
    def __init__(self, config: Config) -> None:
        self._config = config

    def _parse_generic_volume(
        self, volume: str, allow_rw_spec: bool = True, resource_name: str = "volume"
    ) -> Tuple[str, str, bool]:
        parts = volume.split(":")
        read_only = False
        if allow_rw_spec and len(parts) == 4:
            if parts[-1] not in ["ro", "rw"]:
                raise ValueError(f"Wrong ReadWrite/ReadOnly mode spec for '{volume}'")
            read_only = parts.pop() == "ro"
        elif len(parts) != 3:
            raise ValueError(f"Invalid {resource_name} specification '{volume}'")
        container_path = parts.pop()
        raw_uri = ":".join(parts)
        return raw_uri, container_path, read_only

    def volume(self, volume: str) -> Volume:
        raw_uri, container_path, read_only = self._parse_generic_volume(volume)
        storage_uri = uri_from_cli(
            raw_uri,
            self._config.username,
            self._config.cluster_name,
            allowed_schemes=("storage",),
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
            raw_uri, container_path, _ = self._parse_generic_volume(
                volume, allow_rw_spec=False, resource_name="secret file"
            )
            secret_uri = self._parse_secret_resource(raw_uri)
            secret_files.append(SecretFile(secret_uri, container_path))
        return secret_files

    def _parse_secret_resource(self, uri: str) -> URL:
        return uri_from_cli(
            uri,
            self._config.username,
            self._config.cluster_name,
            allowed_schemes=("secret",),
        )

    def _build_disk_volumes(self, input_volumes: Set[str]) -> List[DiskVolume]:
        disk_volumes: List[DiskVolume] = []
        for volume in input_volumes:
            raw_uri, container_path, read_only = self._parse_generic_volume(
                volume, allow_rw_spec=True, resource_name="disk volume"
            )
            disk_uri = self._parse_disk_resource(raw_uri)
            disk_volumes.append(DiskVolume(disk_uri, container_path, read_only))
        return disk_volumes

    def _parse_disk_resource(self, uri: str) -> URL:
        return uri_from_cli(
            uri,
            self._config.username,
            self._config.cluster_name,
            allowed_schemes=("disk",),
        )

    @property
    def _image_parser(self) -> _ImageNameParser:
        registry = {
            cluster.name: cluster.registry_url
            for cluster in self._config.clusters.values()
        }
        return _ImageNameParser(
            self._config.username, self._config.cluster_name, registry
        )

    def local_image(self, image: str) -> LocalImage:
        return self._image_parser.parse_as_local_image(image)

    def remote_image(
        self, image: str, *, tag_option: TagOption = TagOption.DEFAULT
    ) -> RemoteImage:
        return self._image_parser.parse_remote(image, tag_option=tag_option)

    def _local_to_remote_image(self, image: LocalImage) -> RemoteImage:
        return self._image_parser.convert_to_neuro_image(image)

    def _remote_to_local_image(self, image: RemoteImage) -> LocalImage:
        return self._image_parser.convert_to_local_image(image)

    def env(
        self, env: Sequence[str], env_file: Sequence[str] = ()
    ) -> Tuple[Dict[str, str], Dict[str, URL]]:
        warnings.warn(
            "client.parse.env() method is deprecated and scheduled for removal "
            "in future Neuro CLI release, please use client.parse.envs() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        ret = self.envs(env, env_file)
        return ret.env, ret.secret_env

    def envs(self, env: Sequence[str], env_file: Sequence[str] = ()) -> EnvParseResult:
        env_dict = self._build_env(env, env_file)
        secret_env_dict = self._extract_secret_env(env_dict)
        return EnvParseResult(
            env=env_dict,
            secret_env=secret_env_dict,
        )

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

    def volumes(self, volume: Sequence[str]) -> VolumeParseResult:
        input_secret_files = {vol for vol in volume if vol.startswith("secret:")}
        input_disk_volumes = {vol for vol in volume if vol.startswith("disk:")}
        input_volumes = set(volume) - input_secret_files - input_disk_volumes
        return VolumeParseResult(
            volumes=self._build_volumes(input_volumes),
            secret_files=self._build_secret_files(input_secret_files),
            disk_volumes=self._build_disk_volumes(input_disk_volumes),
        )


def _read_lines(env_file: str) -> Iterator[str]:
    with open(env_file, encoding="utf-8-sig") as ef:
        lines = ef.read().splitlines()
    for line in lines:
        line = line.lstrip()
        if line and not line.startswith("#"):
            yield line
