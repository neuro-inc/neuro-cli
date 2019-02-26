import abc
import asyncio
import logging
import ssl
import time
import types
from typing import Any, Callable, Dict, Optional, Type

import aiohttp
import certifi
import pkg_resources

from neuromation.cli.rc import NO_VERSION, ConfigFactory


log = logging.getLogger(__name__)


class AbstractVersionChecker(abc.ABC):
    @abc.abstractmethod
    async def close(self) -> None:  # pragma: no cover
        pass

    @abc.abstractmethod
    async def run(self) -> None:  # pragma: no cover
        pass

    @abc.abstractmethod
    async def update_latest_version(self) -> None:  # pragma: no cover
        pass


class DummyVersionChecker(AbstractVersionChecker):
    async def close(self) -> None:
        pass

    async def run(self) -> None:
        pass

    async def update_latest_version(self) -> None:
        pass


class VersionChecker(AbstractVersionChecker):
    def __init__(
        self,
        connector: Optional[aiohttp.TCPConnector] = None,
        timer: Callable[[], float] = time.time,
    ) -> None:
        if connector is None:
            ssl_context = ssl.SSLContext()
            ssl_context.load_verify_locations(capath=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
        self._session = aiohttp.ClientSession(connector=connector)
        self._timer = timer

    async def close(self) -> None:
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
        try:
            async with self:
                await self.update_latest_version()
        except asyncio.CancelledError:
            raise
        except aiohttp.ClientConnectionError:
            log.debug("IO error on fetching data from PyPI", exc_info=True)
        except Exception:  # pragma: no cover
            log.exception("Error on fetching data from PyPI")

    async def update_latest_version(self) -> None:
        pypi_version = await self._fetch_pypi()
        ConfigFactory.update_last_checked_version(pypi_version, int(self._timer()))

    async def _fetch_pypi(self) -> Any:
        async with self._session.get("https://pypi.org/pypi/neuromation/json") as resp:
            if resp.status != 200:
                log.debug("%s status on fetching PyPI", resp.status)
                return NO_VERSION
            data = await resp.json()
        return self._get_max_version(data)

    def _get_max_version(self, pypi_response: Dict[str, Any]) -> Any:
        try:
            ret = [
                pkg_resources.parse_version(version)
                for version in pypi_response["releases"].keys()
            ]
            return max(ver for ver in ret if not ver.is_prerelease)  # type: ignore
        except (KeyError, ValueError):
            return NO_VERSION
