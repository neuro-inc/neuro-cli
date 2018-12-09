import aiohttp
from typing import Union
from yarl import URL

from .api import API
from .jobs import Jobs


DEFAULT_TIMEOUT = aiohttp.ClientTimeout(None, None, 30, 30)  # type: ignore


class ClientV2:
    def __init__(
        self,
        url: Union[URL, str],
        token: str,
        *,
        timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT,  # type: ignore
    ) -> None:
        if isinstance(url, str):
            url = URL(url)
        self._api = API(url, token, timeout)
        self._jobs = Jobs(self._api)

    async def close(self) -> None:
        await self._api.close()

    @property
    def jobs(self) -> Jobs:
        return self._jobs
