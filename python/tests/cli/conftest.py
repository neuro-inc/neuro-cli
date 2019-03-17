import logging
from collections import namedtuple
from typing import List

import pytest

from neuromation.cli import main, rc

SysCap = namedtuple("SysCap", "out err")
log = logging.getLogger(__name__)


@pytest.fixture()
def config():
    return rc.Config(
        url="https://dev.neu.ro/api/v1", registry_url="https://registry-dev.neu.ro"
    )


@pytest.fixture()
def run_cli(config, capfd, monkeypatch, tmp_path) -> SysCap:
    def _run_cli(arguments: List[str]):
        def _temp_config():
            config_path = tmp_path / ".nmrc"
            rc.save(config_path, config)
            return config_path

        log.info("Run 'neuro %s'", " ".join(arguments))
        try:

            with monkeypatch.context() as ctx:
                ctx.setattr(rc.ConfigFactory, "get_path", _temp_config)
                main(
                    ["--show-traceback", "--disable-pypi-version-check", "--color=no"]
                    + arguments
                )
        except SystemExit:
            pass
        out, err = capfd.readouterr()
        return SysCap(out.strip(), err.strip())

    return _run_cli
