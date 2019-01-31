import logging
from distutils.version import LooseVersion
from typing import Any, Dict, List, Optional

import aiohttp

import neuromation
from neuromation.cli import rc
from neuromation.cli.rc import ConfigFactory


log = logging.getLogger(__name__)


async def warn_if_has_newer_version(config: rc.Config) -> None:
    current_version = get_current_version()
    latest_version = await get_latest_version(config)
    if current_version < latest_version:
        print_update_warning(current_version, latest_version)


def get_current_version() -> LooseVersion:
    return LooseVersion(neuromation.__version__)


async def get_latest_version(config: rc.Config) -> LooseVersion:
    latest_version = config.last_checked_version
    if latest_version is None:
        timeout = aiohttp.ClientTimeout(None, None, 30, 30)
        latest_version = await get_latest_version_from_pypi(timeout)
        if not latest_version:
            raise ValueError("Could not get the latest version from PyPI")
        ConfigFactory.update_last_checked_version(latest_version.vstring)
    return latest_version


def print_update_warning(current: LooseVersion, latest: LooseVersion) -> None:
    update_command = "pip install --upgrade neuromation"
    log.warning(
        f"You are using Neuromation Platform Client version {current}, "
        f"however version {latest} is available. "
    )
    log.warning(f"You should consider upgrading via the '{update_command}' command.")


async def get_latest_version_from_pypi(
    timeout: aiohttp.ClientTimeout
) -> Optional[LooseVersion]:
    response = await request_pypi(timeout)
    if response:
        return max(get_versions(response))


def get_versions(pypi_response: Dict[str, Any]) -> List[LooseVersion]:
    return [LooseVersion(version) for version in pypi_response["releases"].keys()]


# make a fake server:
async def request_pypi(timeout: aiohttp.ClientTimeout) -> Optional[Dict[str, Any]]:
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get("https://pypi.org/pypi/neuromation/json") as response:
            if response.status == 200:
                return await response.json()
