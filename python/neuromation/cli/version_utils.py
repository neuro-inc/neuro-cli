import asyncio
import logging
import time
import types
from typing import Any, Dict, Optional, Type, Callable
import pkg_resources

import aiohttp

from neuromation.cli.rc import ConfigFactory


log = logging.getLogger(__name__)


class VersionChecker:
    def __init__(self, connector: Optional[aiohttp.TCPConnector] = None,
                 timer: Callable[[], float] = time.time) -> None:
        if connector is None:
            connector = aiohttp.TCPConnector()
        self._session = aiohttp.ClientSession(connector=connector)
        self._timer = timer

    async def close(self):
        await self._session.close()

    async def __aenter__(self) -> "VersionChecker":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        exc_tb: Optional[types.TracebackType],
    ) -> None:
        await self.close()

    async def run(self) -> None:
        async with self:
            await self.get_latest_version()

    async def get_latest_version(self) -> None:
        try:
            async with self._session.get(
                "https://pypi.org/pypi/neuromation/json"
            ) as resp:
                if resp.status != 200:
                    log.debug("%s status on fetching PyPI", resp.status)
                    return
                data = await resp.json()
            pypi_version = self._get_max_version(data)
            ConfigFactory.update_last_checked_version(pypi_version, int(self._timer()))
        except asyncio.CancelledError:
            pass
        except aiohttp.ClientConnectionError:
            log.debug("IO error on fetching data from PyPI", exc_info=True)
        except Exception:
            log.exception("Error on fetching data from PyPI")

    def _get_max_version(self, pypi_response: Dict[str, Any]) -> Any:
        try:
            ret = [
                pkg_resources.parse_version(version) for version in pypi_response["releases"].keys()
            ]
            return max(ver for ver in ret if not ver.is_prerelease)
        except ValueError:
            return pkg_resources.parse_version("0.0.0")
