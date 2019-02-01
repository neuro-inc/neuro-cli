import logging
import types
from distutils.version import LooseVersion
from typing import Any, Dict, List, Optional, Type

import aiohttp

from neuromation.cli import rc
from neuromation.cli.rc import ConfigFactory


log = logging.getLogger(__name__)


class VersionChecker:
    def __init__(self, connector: Optional[aiohttp.TCPConnector] = None) -> None:
        if connector is None:
            connector = aiohttp.TCPConnector()
        self._session = aiohttp.ClientSession(connector=connector)

    async def close(self):
        await self._session.close()

    async def __aenter__(self) -> "VersionChecker":
        return self

    async def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        exc_tb: Optional[types.TracebackType],
    ) -> None:
        await self.close()

    async def get_latest_version(self, config: rc.Config) -> LooseVersion:
        try:
            async with self._session
        except:
            pass
        latest_version = LooseVersion(config.last_checked_version)
        if latest_version is None:
            # TODO (ajsuzwkowski 31.1.2019) Save a timestamp when the version was checked
            latest_version = await get_latest_version_from_pypi()
            if not latest_version:
                raise ValueError("Could not get the latest version from PyPI")
            ConfigFactory.update_last_checked_version(latest_version.vstring)
        return latest_version

    async def get_latest_version_from_pypi(self) -> Optional[LooseVersion]:
        response = await request_pypi()
        if response:
            return max(get_versions(response))

    def get_versions(self, pypi_response: Dict[str, Any]) -> List[LooseVersion]:
        return [LooseVersion(version) for version in pypi_response["releases"].keys()]

    async def request_pypi(self) -> Optional[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://pypi.org/pypi/neuromation/json") as response:
                if response.status == 200:
                    return await response.json()
