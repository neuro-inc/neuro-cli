import logging
from dataclasses import dataclass
from typing import Any, Dict

import pkg_resources
from yarl import URL

import neuromation

from .login import _AuthConfig, _AuthToken, _ClusterConfig


log = logging.getLogger(__name__)


@dataclass
class _PyPIVersion:
    NO_VERSION = pkg_resources.parse_version("0.0.0")

    pypi_version: Any
    check_timestamp: int

    def warn_if_has_newer_version(self) -> None:
        current = pkg_resources.parse_version(neuromation.__version__)
        if current < self.pypi_version:
            update_command = "pip install --upgrade neuromation"
            log.warning(
                f"You are using Neuromation Platform Client version {current}, "
                f"however version {self.pypi_version} is available. "
            )
            log.warning(
                f"You should consider upgrading via the '{update_command}' command."
            )
            log.warning("")  # tailing endline

    @classmethod
    def create_uninitialized(cls) -> "_PyPIVersion":
        return cls(cls.NO_VERSION, 0)

    @classmethod
    def from_config(cls, data: Dict[str, Any]) -> "_PyPIVersion":
        try:
            pypi_version = pkg_resources.parse_version(data["pypi_version"])
            check_timestamp = int(data["check_timestamp"])
        except (KeyError, TypeError, ValueError):
            # config has invalid/missing data, ignore it
            pypi_version = cls.NO_VERSION
            check_timestamp = 0
        return cls(pypi_version=pypi_version, check_timestamp=check_timestamp)

    def to_config(self) -> Dict[str, Any]:
        return {
            "pypi_version": str(self.pypi_version),
            "check_timestamp": int(self.check_timestamp),
        }


@dataclass(frozen=True)
class _Config:
    auth_config: _AuthConfig
    auth_token: _AuthToken
    cluster_config: _ClusterConfig
    pypi: _PyPIVersion
    url: URL

    def check_initialized(self) -> None:
        if (
            not self.auth_config.is_initialized()
            or not self.cluster_config.is_initialized()
        ):
            raise ValueError("Missing server configuration, need to login")
