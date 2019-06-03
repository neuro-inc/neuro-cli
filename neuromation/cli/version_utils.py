import abc
import asyncio
import dataclasses
import logging
import ssl
import time
import types
from typing import Any, Callable, Dict, Optional, Type

import aiohttp
import certifi
import pkg_resources
from yarl import URL

from neuromation.api.config import _PyPIVersion


log = logging.getLogger(__name__)


class AbstractVersionChecker(abc.ABC):
    def __init__(self, pypi_version: _PyPIVersion) -> None:
        self._version = pypi_version

    @property
    def version(self) -> _PyPIVersion:
        return self._version

    @abc.abstractmethod
    async def close(self) -> None:  # pragma: no cover
        pass

    @abc.abstractmethod
    async def run(self) -> None:  # pragma: no cover
        pass


class DummyVersionChecker(AbstractVersionChecker):
    async def close(self) -> None:
        pass

    async def run(self) -> None:
        pass


class VersionChecker(AbstractVersionChecker):
    def __init__(
        self,
        pypi_version: _PyPIVersion,
        connector: Optional[aiohttp.TCPConnector] = None,
        timer: Callable[[], float] = time.time,
    ) -> None:
        self._version = pypi_version
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
            loop = asyncio.get_event_loop()
            task1 = loop.create_task(self._update_self_version())
            task2 = loop.create_task(self._update_certifi_version())
            await asyncio.gather(task1, task2)
        except asyncio.CancelledError:
            raise
        except aiohttp.ClientConnectionError:
            log.debug("IO error on fetching data from PyPI", exc_info=True)
        except Exception:  # pragma: no cover
            log.exception("Error on fetching data from PyPI")

    async def _update_self_version(self) -> None:
        pypi_version = await self._fetch_pypi("neuromation")
        self._version = dataclasses.replace(
            self._version, pypi_version=pypi_version, check_timestamp=self._timer()
        )

    async def _update_certifi_version(self) -> None:
        pypi_version = await self._fetch_pypi("certifi")
        self._version = dataclasses.replace(
            self._version,
            certifi_pypi_version=pypi_version,
            certifi_check_timestamp=self._timer(),
        )

    async def _fetch_pypi(self, package: str) -> Any:
        url = URL(f"https://pypi.org/pypi/{package}/json")
        async with self._session.get(url) as resp:
            if resp.status != 200:
                log.debug("%s status on fetching %s", resp.status, url)
                return _PyPIVersion.NO_VERSION
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
            return _PyPIVersion.NO_VERSION
