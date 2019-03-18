import logging
from collections import namedtuple
from typing import List

import pytest

from neuromation.cli import main, rc
from neuromation.cli.const import EX_OK
from neuromation.cli.rc import AuthToken


SysCapWithCode = namedtuple("SysCapWithCode", ["out", "err", "code"])
log = logging.getLogger(__name__)


@pytest.fixture()
def config(token):
    return rc.Config(
        url="https://dev.neu.ro/api/v1",
        registry_url="https://registry-dev.neu.ro",
        auth_token=AuthToken.create_non_expiring(token),
    )


@pytest.fixture()
def run_cli(config, capfd, monkeypatch, tmp_path) -> SysCapWithCode:
    def _run_cli(arguments: List[str]):
        def _temp_config():
            config_path = tmp_path / ".nmrc"
            rc.save(config_path, config)
            return config_path

        log.info("Run 'neuro %s'", " ".join(arguments))
        code = EX_OK
        try:
            with monkeypatch.context() as ctx:
                ctx.setattr(rc.ConfigFactory, "get_path", _temp_config)
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
