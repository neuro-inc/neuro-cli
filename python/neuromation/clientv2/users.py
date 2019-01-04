from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from aiohttp.web_exceptions import HTTPCreated
from yarl import URL

from ..client import ClientError
from .api import API


@dataclass(frozen=True)
class User:
    name: str


class Action(str, Enum):
    READ = "read"
    WRITE = "write"
    MANAGE = "manage"


@dataclass(frozen=True)
class Permission:
    uri: URL
    action: Action

    @classmethod
    def from_cli(cls, username: str, uri: URL, action: Action) -> "Permission":
        if not uri.scheme:
            raise ValueError(
                "URI Scheme not specified. "
                "Please specify one of storage, image, job."
            )
        if uri.scheme not in ["storage", "image", "job"]:
            raise ValueError(
                f"Unsupported URI scheme: {uri.scheme or 'Empty'}. "
                "Please specify one of storage, image, job."
            )
        if not uri.host:
            uri = URL(f"{uri.scheme}://{username}/") / uri.path.lstrip("/")
        return Permission(uri=uri, action=action)

    def to_api(self) -> Dict[str, Any]:
        primitive: Dict[str, Any] = {"uri": str(self.uri), "action": self.action.value}
        return primitive


class Users:
    def __init__(self, api: API) -> None:
        self._api = api

    async def share(self, user: User, permission: Permission) -> None:
        url = URL(f"users/{user.name}/permissions")
        payload = [permission.to_api()]
        async with self._api.request("POST", url, json=payload) as resp:
            #  TODO: server part contain TODO record for returning more then
            #  HTTPCreated, this part must me refactored then
            if resp.status != HTTPCreated.status_code:
                raise ClientError("Server return unexpected result.")
        return None
