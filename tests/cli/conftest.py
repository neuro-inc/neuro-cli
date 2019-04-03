import logging
from collections import namedtuple
from typing import List

import pytest

from neuromation.cli import main, rc
from neuromation.cli.const import EX_OK
from neuromation.cli.rc import ENV_NAME as CFG_ENV_NAME, AuthToken, save as save_config


SysCapWithCode = namedtuple("SysCapWithCode", ["out", "err", "code"])
log = logging.getLogger(__name__)


@pytest.fixture()
def nmrc_path(tmp_path, monkeypatch):
    nmrc_path = tmp_path / "conftest.nmrc"
    monkeypatch.setenv(CFG_ENV_NAME, str(nmrc_path))
    rc.ConfigFactory.set_path(nmrc_path)
    return nmrc_path


@pytest.fixture()
def config(token, nmrc_path):
    cfg = rc.Config(
        url="https://dev.neu.ro/api/v1",
        registry_url="https://registry-dev.neu.ro",
        auth_token=AuthToken.create_non_expiring(token),
    )
    save_config(nmrc_path, cfg)
    return cfg


@pytest.fixture()
def run_cli(config, capfd, tmp_path) -> SysCapWithCode:
    def _run_cli(arguments: List[str]):

        log.info("Run 'neuro %s'", " ".join(arguments))
        code = EX_OK
        try:
            main(
                ["--show-traceback", "--disable-pypi-version-check", "--color=no"]
                + arguments
            )
        except SystemExit as e:
            code = e.code
            pass
        out, err = capfd.readouterr()
        return SysCapWithCode(out.strip(), err.strip(), code)

    return _run_cli
