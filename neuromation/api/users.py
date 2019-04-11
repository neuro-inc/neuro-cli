from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from aiohttp.web import HTTPCreated
from jose import JWTError, jwt
from yarl import URL

from .core import ClientError, _Core


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


class _Users:
    def __init__(self, core: _Core) -> None:
        self._core = core

    async def share(self, user: str, permission: Permission) -> None:
        url = URL(f"users/{user}/permissions")
        payload = [permission.to_api()]
        async with self._core.request("POST", url, json=payload) as resp:
            #  TODO: server part contain TODO record for returning more then
            #  HTTPCreated, this part must me refactored then
            if resp.status != HTTPCreated.status_code:
                raise ClientError("Server return unexpected result.")  # NOQA
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
