from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Sequence

from aiohttp.web import HTTPCreated, HTTPNoContent
from jose import JWTError, jwt
from yarl import URL

from .core import ClientError, _Core
from .utils import NoPublicConstructor


JWT_IDENTITY_CLAIM = "https://platform.neuromation.io/user"
JWT_IDENTITY_CLAIM_OPTIONS = ("identity", JWT_IDENTITY_CLAIM)


class Action(str, Enum):
    READ = "read"
    WRITE = "write"
    MANAGE = "manage"


@dataclass(frozen=True)
class Permission:
    uri: URL
    action: Action

    def to_api(self) -> Dict[str, Any]:
        primitive: Dict[str, Any] = {"uri": str(self.uri), "action": self.action.value}
        return primitive


@dataclass(frozen=True)
class SharedPermission:
    username: str
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

    async def get_shared_acl(
        self, user: str, scheme: Optional[str] = None
    ) -> Sequence[SharedPermission]:
        url = URL(f"users/{user}/permissions/shared")
        params = {"scheme": scheme} if scheme else {}
        async with self._core.request("GET", url, params=params) as resp:
            payload = await resp.json()
        ret = []
        for item in payload:
            uri = URL(item["uri"])
            action = Action(item["action"])
            ret.append(SharedPermission(item["user"], Permission(uri, action)))
        return ret

    async def share(self, user: str, permission: Permission) -> None:
        url = URL(f"users/{user}/permissions")
        payload = [permission.to_api()]
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


def get_token_username(token: str) -> str:
    try:
        claims = jwt.get_unverified_claims(token)
    except JWTError as e:
        raise ValueError(f"Passed string does not contain valid JWT structure.") from e
    for identity_claim in JWT_IDENTITY_CLAIM_OPTIONS:
        if identity_claim in claims:
            return claims[identity_claim]
    raise ValueError("JWT Claims structure is not correct.")
