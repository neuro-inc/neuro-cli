import base64
from typing import Dict

import aiohttp
from yarl import URL

from .core import _Core


TIMEOUT = aiohttp.ClientTimeout(None, None, 30, 30)


class _Registry(_Core):
    """Transport provider for registry client.

    Internal class.
    """

    def __init__(
        self, connector: aiohttp.BaseConnector, base_url: URL, token: str, username: str
    ) -> None:
        self._username = username
        super().__init__(connector, base_url, token, None, TIMEOUT)

    def _auth_headers(self) -> Dict[str, str]:
        assert self._username
        basic = base64.b64encode(
            f"{self._username}:{self._token}".encode("ascii")
        ).decode("ascii")
        return {"Authorization": f"Basic {basic}"}
