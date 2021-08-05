import enum
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncIterator, Mapping, Optional

from dateutil.parser import isoparse
from yarl import URL

from .config import Config
from .core import _Core
from .errors import NDJSONError
from .utils import NoPublicConstructor, asyncgeneratorcontextmanager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Bucket:
    id: str
    owner: str
    cluster_name: str
    provider: "Bucket.Provider"
    credentials: Mapping[str, str]
    created_at: datetime
    name: Optional[str] = None

    @property
    def uri(self) -> URL:
        return URL(f"blob://{self.cluster_name}/{self.owner}/{self.id}")

    class Provider(str, enum.Enum):
        AWS = "aws"


class Buckets(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: Config) -> None:
        self._core = core
        self._config = config

    def _parse_bucket_payload(self, payload: Mapping[str, Any]) -> Bucket:
        return Bucket(
            id=payload["id"],
            owner=payload["owner"],
            name=payload.get("name"),
            created_at=isoparse(payload["created_at"]),
            provider=Bucket.Provider(payload["provider"]),
            cluster_name=self._config.cluster_name,
            credentials=payload["credentials"],
        )

    def _get_buckets_url(self, cluster_name: Optional[str]) -> URL:
        if cluster_name is None:
            cluster_name = self._config.cluster_name
        return self._config.get_cluster(cluster_name).buckets_url

    @asyncgeneratorcontextmanager
    async def list(self, cluster_name: Optional[str] = None) -> AsyncIterator[Bucket]:
        url = self._get_buckets_url(cluster_name)
        auth = await self._config._api_auth()
        headers = {"Accept": "application/x-ndjson"}
        async with self._core.request("GET", url, headers=headers, auth=auth) as resp:
            if resp.headers.get("Content-Type", "").startswith("application/x-ndjson"):
                async for line in resp.content:
                    server_message = json.loads(line)
                    if "error" in server_message:
                        raise NDJSONError(server_message["error"])
                    yield self._parse_bucket_payload(server_message)
            else:
                ret = await resp.json()
                for bucket_data in ret:
                    yield self._parse_bucket_payload(bucket_data)

    async def create(
        self,
        name: Optional[str] = None,
        cluster_name: Optional[str] = None,
    ) -> Bucket:
        url = self._get_buckets_url(cluster_name)
        auth = await self._config._api_auth()
        data = {
            "name": name,
        }
        async with self._core.request("POST", url, auth=auth, json=data) as resp:
            payload = await resp.json()
            return self._parse_bucket_payload(payload)

    async def get(
        self, bucket_id_or_name: str, cluster_name: Optional[str] = None
    ) -> Bucket:
        url = self._get_buckets_url(cluster_name) / bucket_id_or_name
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, auth=auth) as resp:
            payload = await resp.json()
            return self._parse_bucket_payload(payload)

    async def rm(
        self, bucket_id_or_name: str, cluster_name: Optional[str] = None
    ) -> None:
        url = self._get_buckets_url(cluster_name) / bucket_id_or_name
        auth = await self._config._api_auth()
        async with self._core.request("DELETE", url, auth=auth):
            pass
