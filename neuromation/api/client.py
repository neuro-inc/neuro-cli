from pathlib import Path
from types import TracebackType
from typing import Mapping, Optional, Type

import aiohttp

from neuromation.api.quota import _Quota

from .admin import _Admin
from .blob_storage import BlobStorage
from .config import Config
from .core import _Core
from .images import Images
from .jobs import Jobs
from .parser import Parser
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
            self._core._post_init(db, self._config.storage_url)
        self._parser = Parser._create(self._config)
        self._admin = _Admin._create(self._core, self._config)
        self._jobs = Jobs._create(self._core, self._config, self._parser)
        self._blob_storage = BlobStorage._create(self._core, self._config)
        self._storage = Storage._create(self._core, self._config)
        self._users = Users._create(self._core, self._config)
        self._quota = _Quota._create(self._core, self._config)
        self._images: Optional[Images] = None

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        with self._config._open_db() as db:
            self._core._save_cookie(db)
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
    def parse(self) -> Parser:
        return self._parser
