from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Sequence

from aiohttp.web import HTTPCreated, HTTPNoContent
from yarl import URL

from .config import Config
from .core import _Core
from .errors import ClientError
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
    def __init__(self, core: _Core, config: Config) -> None:
        self._core = core
        self._config = config

    async def get_acl(
        self, user: str, scheme: Optional[str] = None, *, uri: Optional[URL] = None
    ) -> Sequence[Permission]:
        url = self._get_user_url(user) / "permissions"
        if scheme:
            if uri is not None:
                raise ValueError("Conflicting arguments 'uri' and 'scheme'")
            uri = URL.build(scheme=scheme)
        params = {"uri": str(uri)} if uri is not None else {}
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, params=params, auth=auth) as resp:
            payload = await resp.json()
        ret = []
        for item in payload:
            uri = URL(item["uri"])
            action = Action(item["action"])
            ret.append(Permission(uri, action))
        return ret

    async def get_shares(
        self, user: str, scheme: Optional[str] = None, *, uri: Optional[URL] = None
    ) -> Sequence[Share]:
        url = self._get_user_url(user) / "permissions" / "shared"
        if scheme:
            if uri is not None:
                raise ValueError("Conflicting arguments 'uri' and 'scheme'")
            uri = URL.build(scheme=scheme)
        params = {"uri": str(uri)} if uri is not None else {}
        auth = await self._config._api_auth()
        async with self._core.request("GET", url, params=params, auth=auth) as resp:
            payload = await resp.json()
        ret = []
        for item in payload:
            uri = URL(item["uri"])
            action = Action(item["action"])
            ret.append(Share(item["user"], Permission(uri, action)))
        return ret

    async def share(self, user: str, permission: Permission) -> None:
        url = self._get_user_url(user) / "permissions"
        payload = [_permission_to_api(permission)]
        auth = await self._config._api_auth()
        async with self._core.request("POST", url, json=payload, auth=auth) as resp:
            #  TODO: server part contain TODO record for returning more then
            #  HTTPCreated, this part must me refactored then
            if resp.status != HTTPCreated.status_code:
                raise ClientError("Server return unexpected result.")
        return None

    async def revoke(self, user: str, uri: URL) -> None:
        url = self._get_user_url(user) / "permissions"
        auth = await self._config._api_auth()
        async with self._core.request(
            "DELETE", url, params={"uri": str(uri)}, auth=auth
        ) as resp:
            #  TODO: server part contain TODO record for returning more then
            #  HTTPNoContent, this part must me refactored then
            if resp.status != HTTPNoContent.status_code:
                raise ClientError(f"Server return unexpected result: {resp.status}.")
        return None

    async def add(self, role_name: str) -> None:
        url = self._config.api_url / "users"
        auth = await self._config._api_auth()
        async with self._core.request(
            "POST", url, json={"name": role_name}, auth=auth
        ) as resp:
            if resp.status != HTTPCreated.status_code:
                raise ClientError(f"Server return unexpected result: {resp.status}.")
        return None

    async def remove(self, role_name: str) -> None:
        url = self._get_user_url(role_name)
        auth = await self._config._api_auth()
        async with self._core.request("DELETE", url, auth=auth) as resp:
            if resp.status != HTTPNoContent.status_code:
                raise ClientError(f"Server return unexpected result: {resp.status}.")
        return None

    def _get_user_url(self, user: str) -> URL:
        if ":" in user:
            raise ValueError(f"Invalid name: {user!r}")
        return self._config.api_url / "users" / user.replace("/", ":")


def _permission_to_api(perm: Permission) -> Dict[str, Any]:
    primitive: Dict[str, Any] = {"uri": str(perm.uri), "action": perm.action.value}
    return primitive
