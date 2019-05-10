import asyncio
import logging
from collections import namedtuple
from pathlib import Path
from typing import Any, AsyncIterator, Callable, List

import pytest
from yarl import URL

from neuromation.api import Factory
from neuromation.api.config import _AuthConfig, _AuthToken, _Config, _PyPIVersion
from neuromation.cli import main
from neuromation.cli.const import EX_OK
from neuromation.cli.root import Root


SysCapWithCode = namedtuple("SysCapWithCode", ["out", "err", "code"])
log = logging.getLogger(__name__)


@pytest.fixture()
def nmrc_path(tmp_path: Path, token: str, auth_config: _AuthConfig) -> Path:
    nmrc_path = tmp_path / "conftest.nmrc"
    config = _Config(
        auth_config=auth_config,
        auth_token=_AuthToken.create_non_expiring(token),
        pypi=_PyPIVersion.create_uninitialized(),
        url=URL("https://dev.neu.ro/api/v1"),
        registry_url=URL("https://registry-dev.neu.ro"),
    )
    Factory(nmrc_path)._save(config)
    return nmrc_path


@pytest.fixture()
async def root(nmrc_path: Path, loop: asyncio.AbstractEventLoop) -> AsyncIterator[Root]:
    root = Root(
        color=False,
        tty=False,
        terminal_size=(80, 24),
        disable_pypi_version_check=True,
        network_timeout=60,
        config_path=nmrc_path,
    )

    await root.init_client()
    yield root
    await root.close()


@pytest.fixture()
def run_cli(
    nmrc_path: Path, capfd: Any, tmp_path: Path
) -> Callable[[List[str]], SysCapWithCode]:
    def _run_cli(arguments: List[str]) -> SysCapWithCode:
        log.info("Run 'neuro %s'", " ".join(arguments))
        capfd.readouterr()

        code = EX_OK
        try:
            main(
                [
                    "--show-traceback",
                    "--disable-pypi-version-check",
                    "--color=no",
                    f"--neuromation-config={nmrc_path}",
                ]
                + arguments
            )
        except SystemExit as e:
            code = e.code
            pass
        out, err = capfd.readouterr()
        return SysCapWithCode(out.strip(), err.strip(), code)

    return _run_cli


@pytest.fixture()
def click_tty_emulation(monkeypatch: Any) -> None:
    monkeypatch.setattr("click._compat.isatty", lambda stream: True)
