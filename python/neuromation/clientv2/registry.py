from . import API
import aiohttp
import base64
from jose import jwt
from yarl import URL
from async_generator import asynccontextmanager
from typing import  Any, Optional, Dict, AsyncIterator

TIMEOUT = aiohttp.ClientTimeout(None, None, 30, 30)

class Registry(API):
    """Transport provider for registry client.

    Internal class.
    """

    def __init__(self, url: URL, token: str) -> None:
        super().__init__(url, token, TIMEOUT)
        self._token = token
        if token:
            jwt_data = jwt.get_unverified_claims(token)
            username = jwt_data.get("identity", None)
            basic = base64.b64encode(f'{username}:{token}'.encode('ascii')).decode('ascii')
            headers = {"Authorization": f"Basic {basic}"}
            self._legacy_session = self._session
            self._session = aiohttp.ClientSession(timeout=TIMEOUT, headers=headers)
        else:
            self._legacy_session = None

    async def close(self):
        await super().close()
        if self._legacy_session:
            await self._legacy_session.close()