import datetime
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from yarl import URL

from .config import Config
from .core import _Core
from .storage import FileStatus, FileStatusType
from .url_utils import normalize_storage_path_uri
from .users import Action
from .utils import NoPublicConstructor


MAX_OPEN_FILES = 20
READ_SIZE = 2 ** 20  # 1 MiB
TIME_THRESHOLD = 1.0

Printer = Callable[[str], None]
ProgressQueueItem = Optional[Tuple[Callable[[Any], None], Any]]


# We extend from FileStatus to make sure our formatting system from Storage can be
# reused
@dataclass(frozen=True)
class ObjStatus(FileStatus):

    permission: Action = Action.READ


class ObjectStorage(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core, config: Config) -> None:
        self._core = core
        self._config = config
        self._min_time_diff = 0.0
        self._max_time_diff = 0.0

    def _uri_to_path(self, uri: URL) -> str:
        uri = normalize_storage_path_uri(uri, self._config.username)
        prefix = uri.host + "/" if uri.host else ""
        return prefix + uri.path.lstrip("/")

    async def list_buckets(self, *, token: Optional[str] = None) -> List[ObjStatus]:
        url = self._config.obj_url / "b" / ""
        auth = await self._config._api_auth()

        async with self._core.request("GET", url, auth=auth) as resp:
            res = await resp.json()
            return [_obj_status_from_bucket(bucket) for bucket in res]

    async def list_objects(
        self, bucket_name: str, prefix: str = "", recursive: bool = False,
    ) -> List[ObjStatus]:
        url = self._config.obj_url / "o" / bucket_name
        auth = await self._config._api_auth()

        query = {"recursive": str(recursive).lower()}
        if prefix:
            query["prefix"] = prefix
        url = url.with_query(query)

        contents: List[ObjStatus] = []
        common_prefixes: List[ObjStatus] = []
        breakpoint()
        while True:
            async with self._core.request("GET", url, auth=auth) as resp:
                res = await resp.json()
                contents.extend(
                    [_obj_status_from_key(bucket_name, key) for key in res["contents"]]
                )
                common_prefixes.extend(
                    [
                        _obj_status_from_prefix(bucket_name, prefix)
                        for prefix in res["common_prefixes"]
                    ]
                )
                if res["is_truncated"] and res["contents"]:
                    start_after = res["contents"][-1]["key"]
                    url = url.with_query(start_after=start_after)
                else:
                    break
        return common_prefixes + contents


def _format_bucket_uri(bucket_name: str, key: str = "") -> URL:
    return URL.build(scheme="object",)


def _obj_status_from_bucket(data: Dict[str, Any]) -> ObjStatus:
    mtime = datetime.datetime.fromisoformat(data["creation_date"]).timestamp()
    return ObjStatus(
        path=data["name"],
        type=FileStatusType.DIRECTORY,
        size=0,
        modification_time=int(mtime),
    )


def _obj_status_from_key(bucket_name: str, data: Dict[str, Any]) -> ObjStatus:
    return ObjStatus(
        path=data["key"],
        type=FileStatusType.FILE,
        size=int(data["size"]),
        modification_time=int(data["last_modified"]),
    )


def _obj_status_from_prefix(bucket_name: str, data: Dict[str, Any]) -> ObjStatus:
    return ObjStatus(
        path=data["prefix"], type=FileStatusType.DIRECTORY, size=0, modification_time=0,
    )
