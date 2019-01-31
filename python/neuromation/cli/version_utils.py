import logging
from distutils.version import LooseVersion
from typing import Any, Dict, List

import aiohttp

import neuromation
from neuromation.cli import rc
from neuromation.cli.rc import ConfigFactory


log = logging.getLogger(__name__)


async def check_newer_version(config: rc.Config) -> None:
    latest_version = config.last_checked_version
    if latest_version is None:
        timeout = aiohttp.ClientTimeout(None, None, 30, 30)
        latest_version = await get_latest_version_from_pypi(timeout)
        ConfigFactory.update_last_checked_version(latest_version.vstring)

    current_version = get_current_version()
    if current_version < latest_version:
        print_update_version_message(current_version, latest_version)


def print_update_version_message(current: LooseVersion, latest: LooseVersion) -> None:
    update_command = "pip install --upgrade neuromation"
    log.warning(
        f"The newer version {latest} is available (current version: {current}). "
        f"To update please run '{update_command}'"
    )


def get_current_version() -> LooseVersion:
    return LooseVersion(neuromation.__version__)


def get_pypi_versions(pypi_response: Dict[str, Any]) -> List[LooseVersion]:
    return [LooseVersion(version) for version in pypi_response["releases"].keys()]


async def get_latest_version_from_pypi(timeout: aiohttp.ClientTimeout) -> LooseVersion:
    resp = await request_pypi(timeout)
    return max(version for version in get_pypi_versions(resp))


async def request_pypi(timeout: aiohttp.ClientTimeout) -> Dict[str, Any]:
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get("https://pypi.org/pypi/neuromation/json") as response:
            response.raise_for_status()
            return await response.json()
