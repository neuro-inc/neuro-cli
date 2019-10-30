import base64
from typing import Dict, Optional

import aiohttp
from yarl import URL

from .core import _Core


class _Registry(_Core):
    """Transport provider for registry client.

    Internal class.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: URL,
        token: str,
        trace_id: Optional[str],
        username: str,
    ) -> None:
        self._username = username
        super().__init__(session, base_url, token, None, trace_id)

    def _auth_headers(self) -> Dict[str, str]:
        assert self._username
        basic = base64.b64encode(
            f"{self._username}:{self._token}".encode("ascii")
        ).decode("ascii")
        return {"Authorization": f"Basic {basic}"}
