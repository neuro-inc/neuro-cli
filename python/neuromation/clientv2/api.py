from typing import Dict, Optional

import aiohttp
from async_generator import asynccontextmanager
from yarl import URL

from neuromation.client import (
    AuthenticationError,
    AuthorizationError,
    ClientError,
    IllegalArgumentError,
    ResourceNotFound,
)


class API:
    """Transport provider for public API client.

    Internal class.
    """

    def __init__(
        self, url: URL, token: str, timeout: aiohttp.ClientTimeout  # type: ignore
    ) -> None:
        self._url = url
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        self._exception_map = {
            403: AuthorizationError,
            401: AuthenticationError,
            400: IllegalArgumentError,
            404: ResourceNotFound,
            405: ClientError,
        }

    async def close(self) -> None:
        await self._session.close()

    @asynccontextmanager
    async def request(
        self, method: str, rel_url: URL, headers: Optional[Dict[str, str]] = None
    ) -> aiohttp.ClientResponse:
        assert not rel_url.is_absolute()
        url = self._url.join(rel_url)
        async with self._session.request(method, url, headers=headers) as resp:
            try:
                resp.raise_for_status()
            except aiohttp.ClientResponseError as exc:
                code = exc.status
                message = exc.message
                try:
                    error_response = await resp.json()
                    message = error_response["error"]
                except Exception:
                    pass
                err_cls = self._exception_map.get(code, IllegalArgumentError)
                raise err_cls(message)
            else:
                yield resp
