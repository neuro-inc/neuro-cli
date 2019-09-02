from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Sequence

from aiohttp.web import HTTPCreated, HTTPNoContent
from yarl import URL

from .core import ClientError, _Core
from .utils import NoPublicConstructor


class Action(str, Enum):
    READ = "read"
    WRITE = "write"
    MANAGE = "manage"


@dataclass(frozen=True)
class Permission:
    uri: URL
    action: Action


@dataclass(frozen=True)
class Share:
    user: str
    permission: Permission


class Users(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core) -> None:
        self._core = core

    async def get_acl(
        self, user: str, scheme: Optional[str] = None
    ) -> Sequence[Permission]:
        url = URL(f"users/{user}/permissions")
        params = {"scheme": scheme} if scheme else {}
        async with self._core.request("GET", url, params=params) as resp:
            payload = await resp.json()
        ret = []
        for item in payload:
            uri = URL(item["uri"])
            action = Action(item["action"])
            ret.append(Permission(uri, action))
        return ret

    async def get_shares(
        self, user: str, scheme: Optional[str] = None
    ) -> Sequence[Share]:
        url = URL(f"users/{user}/permissions/shared")
        params = {"scheme": scheme} if scheme else {}
        async with self._core.request("GET", url, params=params) as resp:
            payload = await resp.json()
        ret = []
        for item in payload:
            uri = URL(item["uri"])
            action = Action(item["action"])
            ret.append(Share(item["user"], Permission(uri, action)))
        return ret

    async def share(self, user: str, permission: Permission) -> None:
        url = URL(f"users/{user}/permissions")
        payload = [_permission_to_api(permission)]
        async with self._core.request("POST", url, json=payload) as resp:
            #  TODO: server part contain TODO record for returning more then
            #  HTTPCreated, this part must me refactored then
            if resp.status != HTTPCreated.status_code:
                raise ClientError("Server return unexpected result.")  # NOQA
        return None

    async def revoke(self, user: str, uri: URL) -> None:
        url = URL(f"users/{user}/permissions")
        async with self._core.request("DELETE", url, params={"uri": str(uri)}) as resp:
            #  TODO: server part contain TODO record for returning more then
            #  HTTPNoContent, this part must me refactored then
            if resp.status != HTTPNoContent.status_code:
                raise ClientError(
                    f"Server return unexpected result: {resp.status}."
                )  # NOQA
        return None


def _permission_to_api(perm: Permission) -> Dict[str, Any]:
    primitive: Dict[str, Any] = {"uri": str(perm.uri), "action": perm.action.value}
    return primitive
