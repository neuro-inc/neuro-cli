from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, Optional, Tuple

from aiohttp.web import HTTPCreated, HTTPNoContent, HTTPOk
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

    @classmethod
    def from_cli(cls, username: str, uri: URL, action: Action) -> "Permission":
        return Permission(uri=uri_from_cli(username, uri), action=action)

    def to_api(self) -> Dict[str, Any]:
        primitive: Dict[str, Any] = {"uri": str(self.uri), "action": self.action.value}
        return primitive


class Users(metaclass=NoPublicConstructor):
    def __init__(self, core: _Core) -> None:
        self._core = core

    async def list(
        self, user: str, scheme: Optional[str] = None
    ) -> Iterable[Tuple[URL, Action]]:
        url = URL(f"users/{user}/permissions")
        params = {"scheme": scheme} if scheme else {}
        async with self._core.request("GET", url, params=params) as resp:
            if resp.status != HTTPOk.status_code:
                raise ClientError("Server return unexpected result.")  # NOQA
            payload = await resp.json()
        ret = []
        for item in payload:
            uri = URL(item["uri"])
            action = Action(item["action"])
            ret.append((uri, action))
        return ret

    async def list_shared(
        self, user: str, scheme: Optional[str] = None
    ) -> Iterable[Tuple[str, URL, Action]]:
        url = URL(f"users/{user}/permissions/shared")
        params = {"scheme": scheme} if scheme else {}
        async with self._core.request("GET", url, params=params) as resp:
            if resp.status != HTTPOk.status_code:
                raise ClientError("Server return unexpected result.")  # NOQA
            payload = await resp.json()
        ret = []
        for item in payload:
            uri = URL(item["uri"])
            action = Action(item["action"])
            ret.append((item["user"], uri, action))
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


def uri_from_cli(username: str, uri: URL) -> URL:
    if not uri.scheme:
        raise ValueError(
            "URI Scheme not specified. " "Please specify one of storage, image, job."
        )
    if uri.scheme not in ["storage", "image", "job"]:
        raise ValueError(
            f"Unsupported URI scheme: {uri.scheme or 'Empty'}. "
            f"Please specify one of storage, image, job."
        )
    if not uri.host:
        uri = URL(f"{uri.scheme}://{username}/") / uri.path.lstrip("/")
    return uri
