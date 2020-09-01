import os
from dataclasses import dataclass
from typing import Dict, Iterator, Mapping, Optional, Sequence, Set, Tuple

from yarl import URL

from .config import Config
from .parsing_utils import LocalImage, RemoteImage, TagOption, _ImageNameParser
from .url_utils import normalize_storage_path_uri, uri_from_cli
from .users import Users
from .utils import NoPublicConstructor


ROOT_MOUNTPOINT = "/var/neuro"

NEUROMATION_ROOT_ENV_VAR = "NEUROMATION_ROOT"
NEUROMATION_HOME_ENV_VAR = "NEUROMATION_HOME"
RESERVED_ENV_VARS = {NEUROMATION_ROOT_ENV_VAR, NEUROMATION_HOME_ENV_VAR}


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
    def __init__(self, config: Config, users: Users) -> None:
        self._config = config
        self._users = users

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

    async def _build_volumes(
        self, input_volumes: Set[str], env_dict: Dict[str, str]
    ) -> Set[Volume]:
        cluster_name = self._config.cluster_name
        volumes: Set[Volume] = set()

        if "ALL" in input_volumes:
            if len(input_volumes) > 1:
                raise ValueError(
                    f"Cannot use `--volume=ALL` together with other `--volume` options"
                )
            available = await self._users.get_acl(
                self._config.username, scheme="storage"
            )
            for perm in available:
                if perm.uri.host == cluster_name:
                    path = perm.uri.path
                    assert path[0] == "/"
                    volumes.add(
                        Volume(
                            storage_uri=perm.uri,
                            container_path=f"{ROOT_MOUNTPOINT}{path}",
                            read_only=perm.action not in ("write", "manage"),
                        )
                    )
            neuro_mountpoint = _get_neuro_mountpoint(self._config.username)
            env_dict[NEUROMATION_HOME_ENV_VAR] = neuro_mountpoint
            env_dict[NEUROMATION_ROOT_ENV_VAR] = ROOT_MOUNTPOINT
        else:
            if "HOME" in input_volumes:
                raise ValueError("--volume=HOME no longer supported")
            for vol in input_volumes:
                volumes.add(self.volume(vol))
        return volumes

    def _build_secret_files(self, input_volumes: Set[str]) -> Set[SecretFile]:
        secret_files: Set[SecretFile] = set()
        for volume in input_volumes:
            parts = volume.split(":")
            if len(parts) != 3:
                raise ValueError(f"Invalid secret file specification '{volume}'")
            container_path = parts.pop()
            secret_uri = self.parse_secret_resource(":".join(parts))
            secret_files.add(SecretFile(secret_uri, container_path))
        return secret_files

    def parse_secret_resource(self, uri: str) -> URL:
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
        self, env: Sequence[str], env_file: Optional[str]
    ) -> Tuple[Dict[str, str], Mapping[str, URL]]:
        env_dict = self._build_env(env, env_file)
        secret_env_dict = self._extract_secret_env(env_dict)
        return env_dict, secret_env_dict

    def _build_env(self, env: Sequence[str], env_file: Optional[str]) -> Dict[str, str]:
        if env_file:
            env = [*_read_lines(env_file), *env]

        env_dict = {}
        for line in env:
            splitted = line.split("=", 1)
            name = splitted[0]
            if len(splitted) == 1:
                val = os.environ.get(splitted[0], "")
            else:
                val = splitted[1]
            if name in RESERVED_ENV_VARS:
                raise ValueError(
                    f"Unable to re-define system-reserved environment variable: {name}"
                )
            env_dict[name] = val
        return env_dict

    def _extract_secret_env(self, env_dict: Dict[str, str]) -> Dict[str, URL]:
        secret_env_dict = {}
        for name, val in env_dict.copy().items():
            if val.startswith("secret:"):
                secret_env_dict[name] = self.parse_secret_resource(val)
                del env_dict[name]
        return secret_env_dict

    async def volumes(
        self, volume: Sequence[str], env_dict: Dict[str, str]
    ) -> Tuple[Set[Volume], Set[SecretFile]]:
        input_secret_files = {vol for vol in volume if vol.startswith("secret:")}
        input_volumes = set(volume) - input_secret_files
        secret_files = self._build_secret_files(input_secret_files)
        vols = await self._build_volumes(input_volumes, env_dict)
        return vols, secret_files


def _read_lines(env_file: str) -> Iterator[str]:
    with open(env_file, encoding="utf-8-sig") as ef:
        lines = ef.read().splitlines()
    for line in lines:
        line = line.lstrip()
        if line and not line.startswith("#"):
            yield line


def _get_neuro_mountpoint(username: str) -> str:
    return f"{ROOT_MOUNTPOINT}/{username}"
