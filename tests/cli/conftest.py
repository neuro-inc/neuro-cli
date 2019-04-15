import logging
from collections import namedtuple
from typing import List

import pytest
from yarl import URL

from neuromation.api import Factory
from neuromation.api.config import _AuthConfig, _AuthToken, _Config, _PyPIVersion
from neuromation.cli import main
from neuromation.cli.const import EX_OK


SysCapWithCode = namedtuple("SysCapWithCode", ["out", "err", "code"])
log = logging.getLogger(__name__)


@pytest.fixture()
def nmrc_path(tmp_path, token, auth_config):
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
def run_cli(nmrc_path, capfd, tmp_path) -> SysCapWithCode:
    def _run_cli(arguments: List[str]):

        log.info("Run 'neuro %s'", " ".join(arguments))
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
