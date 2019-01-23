import base64
from typing import Union

import aiohttp
from aiohttp import ClientSession
from jose import jwt
from yarl import URL

from . import API


TIMEOUT = aiohttp.ClientTimeout(None, None, 30, 30)


class Registry(API):
    """Transport provider for registry client.

    Internal class.
    """

    def __init__(self, url: URL, token: str) -> None:
        super().__init__(url, token, TIMEOUT)
        self._token = token
        self._legacy_session: Union[ClientSession, None] = None
        if token:
            jwt_data = jwt.get_unverified_claims(token)
            username = jwt_data.get("identity", None)
            basic = base64.b64encode(f"{username}:{token}".encode("ascii")).decode(
                "ascii"
            )
            headers = {"Authorization": f"Basic {basic}"}
            self._legacy_session = self._session
            self._session = aiohttp.ClientSession(timeout=TIMEOUT, headers=headers)

    async def close(self) -> None:
        await super().close()
        if self._legacy_session:
            await self._legacy_session.close()
