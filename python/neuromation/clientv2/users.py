from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from yarl import URL

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
    def from_cli(cls, principal: str, uri: str, action: Action) -> "Permission":
        url = URL(uri)
        if url.scheme not in ["storage", "image", "job"]:
            raise ValueError(f"Unsupported scheme: {url.scheme}")
        if not url.host:
            url = URL(f"{url.scheme}://{principal}/") / url.path.lstrip("/")
        return Permission(uri=url, action=action)

    def to_api(self) -> Dict[str, Any]:
        primitive: Dict[str, Any] = {"uri": str(self.uri), "action": self.action.value}
        return primitive


class Users:
    def __init__(self, api: API) -> None:
        self._api = api

    async def share(self, whom: User, permission: Permission) -> None:
        url = URL(f"users/{whom.name}/permissions")
        payload = list()
        payload.append(permission.to_api())
        async with self._api.request("POST", url, json=payload) as resp:
            await resp.json()
        return None
