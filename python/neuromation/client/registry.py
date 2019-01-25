import base64
from typing import Dict

import aiohttp
from yarl import URL

from . import API


TIMEOUT = aiohttp.ClientTimeout(None, None, 30, 30)


class Registry(API):
    """Transport provider for registry client.

    Internal class.
    """

    def __init__(self, url: URL, token: str, username: str) -> None:
        self._username = username
        super().__init__(url, token, TIMEOUT)

    def _auth_headers(self) -> Dict[str, str]:
        assert self._username
        basic = base64.b64encode(
            f"{self._username}:{self._token}".encode("ascii")
        ).decode("ascii")
        return {"Authorization": f"Basic {basic}"}
