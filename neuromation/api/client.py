import uuid
from pathlib import Path
from types import TracebackType
from typing import Mapping, Optional, Type, Dict, Set, Tuple, List, MutableSequence

import aiohttp
import click
from yarl import URL

from neuromation.api.quota import _Quota

from .admin import _Admin
from .blob_storage import BlobStorage
from .config import Config
from .core import _Core
from .images import Images
from .jobs import Jobs
from .parser import Parser, Volume
from .secrets import Secrets
from .server_cfg import Preset
from .storage import Storage
from .users import Users
from .utils import NoPublicConstructor


class Client(metaclass=NoPublicConstructor):
    def __init__(
        self, session: aiohttp.ClientSession, path: Path, trace_id: Optional[str],
    ) -> None:
        self._closed = False
        self._trace_id = trace_id
        self._session = session
        self._core = _Core(session, trace_id)
        self._config = Config._create(self._core, path)

        # Order does matter, need to check the main config before loading
        # the storage cookie session
        self._config._load()
        with self._config._open_db() as db:
            self._core._post_init(db,)
        self._parser = Parser._create(self._config)
        self._admin = _Admin._create(self._core, self._config)
        self._jobs = Jobs._create(self._core, self._config, self._parser)
        self._blob_storage = BlobStorage._create(self._core, self._config)
        self._storage = Storage._create(self._core, self._config)
        self._users = Users._create(self._core, self._config)
        self._quota = _Quota._create(self._core, self._config)
        self._secrets = Secrets._create(self._core, self._config)
        self._images: Optional[Images] = None

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        with self._config._open_db() as db:
            self._core._save_cookies(db)
        await self._core.close()
        if self._images is not None:
            await self._images._close()
        await self._session.close()

    async def __aenter__(self) -> "Client":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional[TracebackType] = None,
    ) -> None:
        await self.close()

    @property
    def username(self) -> str:
        return self._config.username

    @property
    def cluster_name(self) -> str:
        return self._config.cluster_name

    @property
    def presets(self) -> Mapping[str, Preset]:
        # TODO: add deprecation warning eventually.
        # The preferred API is client.config now.
        return self._config.presets

    @property
    def config(self) -> Config:
        return self._config

    @property
    def jobs(self) -> Jobs:
        return self._jobs

    @property
    def blob_storage(self) -> BlobStorage:
        return self._blob_storage

    @property
    def storage(self) -> Storage:
        return self._storage

    @property
    def users(self) -> Users:
        return self._users

    @property
    def images(self) -> Images:
        if self._images is None:
            self._images = Images._create(self._core, self._config, self._parser)
        return self._images

    @property
    def secrets(self) -> Secrets:
        return self._secrets

    @property
    def parse(self) -> Parser:
        return self._parser

    async def pass_config(
        self, env_dict: Dict[str, str], volumes: List[Volume], quiet: bool
    ) -> None:
        env_name = NEURO_STEAL_CONFIG
        if env_name in env_dict:
            raise ValueError(f"{env_name} is already set to {env_dict[env_name]}")
        env_var, secret_volume = await self.upload_and_map_config(quiet)
        env_dict[NEURO_STEAL_CONFIG] = env_var
        volumes.append(secret_volume)

    async def upload_and_map_config(self, quiet: bool) -> Tuple[str, Volume]:
        # store the Neuro CLI config on the storage under some random path
        nmrc_path = URL(self._config._path.expanduser().resolve().as_uri())
        random_nmrc_filename = f"{uuid.uuid4()}-cfg"
        storage_nmrc_folder = URL(
            f"storage://{self.cluster_name}/{self.username}/.neuro/"
        )
        storage_nmrc_path = storage_nmrc_folder / random_nmrc_filename
        local_nmrc_folder = f"{STORAGE_MOUNTPOINT}/.neuro/"
        local_nmrc_path = f"{local_nmrc_folder}{random_nmrc_filename}"
        if not quiet:
            click.echo(
                f"Temporary config file created on storage: {storage_nmrc_path}."
            )
            click.echo(f"Inside container it will be available at: {local_nmrc_path}.")
        await self.storage.mkdir(storage_nmrc_folder, parents=True, exist_ok=True)

        async def skip_tmp(fname: str) -> bool:
            return not fname.endswith(("-shm", "-wal", "-journal"))

        await self.storage.upload_dir(nmrc_path, storage_nmrc_path, filter=skip_tmp)
        # specify a container volume and mount the storage path
        # into specific container path
        return (
            local_nmrc_path,
            Volume(
                storage_uri=storage_nmrc_folder,
                container_path=local_nmrc_folder,
                read_only=False,
            ),
        )


NEURO_STEAL_CONFIG = "NEURO_STEAL_CONFIG"
STORAGE_MOUNTPOINT = "/var/storage"
