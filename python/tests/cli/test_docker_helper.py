import io
import json
import logging
import re
import sys
from collections import namedtuple
from pathlib import Path
from typing import List

import pytest
from yarl import URL

from neuromation.cli import rc
from neuromation.cli.const import EX_OK
from neuromation.cli.docker_credential_helper import main as dch
from neuromation.cli.rc import ENV_NAME as CFG_ENV_NAME, save as save_config


SysCapWithCode = namedtuple("SysCapWithCode", ["out", "err", "code"])
log = logging.getLogger(__name__)


@pytest.fixture()
def nmrc_anon_path(tmp_path, monkeypatch):
    nmrc_path = tmp_path / "anon.nmrc"
    monkeypatch.setenv(CFG_ENV_NAME, str(nmrc_path))
    return nmrc_path


@pytest.fixture()
def config_anon(token, nmrc_anon_path):
    cfg = rc.Config(
        url="https://dev.neu.ro/api/v1", registry_url="https://registry-dev.neu.ro"
    )
    save_config(nmrc_anon_path, cfg)
    return cfg


@pytest.fixture()
def run_dch(
    capfd, monkeypatch, tmp_path, config_anon, config, nmrc_anon_path, nmrc_path
) -> SysCapWithCode:
    def _run_dch(arguments: List[str], anon=False):

        log.info("Run 'docker-helper-neuro %s'", " ".join(arguments))
        code = EX_OK
        try:
            old_config_path = rc.ConfigFactory.get_path()
            with monkeypatch.context() as ctx:
                ctx.setattr(sys, "argv", ["docker-credential-helper"] + arguments)
                if anon:
                    rc.ConfigFactory.set_path(nmrc_anon_path)
                else:
                    rc.ConfigFactory.set_path(nmrc_path)

                dch()
        except SystemExit as e:
            code = e.code
            pass
        finally:
            rc.ConfigFactory.set_path(old_config_path)
        out, err = capfd.readouterr()
        return SysCapWithCode(out.strip(), err.strip(), code)

    return _run_dch


class TestCli:
    def test_path_not_exists(self, run_cli, tmp_path: Path):
        path = tmp_path / "some" / "not-exists"
        json_path = path / "config.json"
        capture = run_cli(["config", "docker", "--config", str(path)])
        assert not capture.err
        assert json_path.is_file()

    def test_path_is_not_dir(self, run_cli, tmp_path: Path):
        path = tmp_path / "file"
        with path.open("w") as file:
            file.write("text")
        captured = run_cli(["config", "docker", "--config", str(path)])
        assert re.match(r"Specified path is not a directory", captured.out)

    def test_path_from_env(self, run_cli, tmp_path, config, monkeypatch):
        json_path = tmp_path / "config.json"
        with json_path.open("w") as file:
            file.write("{}")
        monkeypatch.setenv("DOCKER_CONFIG", str(tmp_path))
        capture = run_cli(["config", "docker"])
        assert not capture.err
        assert json_path.is_file()
        with json_path.open() as fp:
            payload = json.load(fp)
        registry = URL(config.registry_url).host
        assert payload["credHelpers"] == {registry: "neuro"}

    def test_new_file(self, run_cli, tmp_path: Path, config):
        path = tmp_path / ".docker"
        json_path = path / "config.json"
        capture = run_cli(["config", "docker", "--config", str(path)])
        assert not capture.err
        assert json_path.is_file()
        with json_path.open() as fp:
            payload = json.load(fp)
        registry = URL(config.registry_url).host
        assert payload["credHelpers"] == {registry: "neuro"}

    def test_merge_file_without_helpers(self, run_cli, tmp_path: Path, config):
        path = tmp_path / ".docker"
        path.mkdir()
        json_path = path / "config.json"
        with json_path.open("w") as fp:
            json.dump({"test": "value"}, fp)
        capture = run_cli(["config", "docker", "--config", str(path)])
        assert not capture.err
        assert json_path.is_file()
        with json_path.open() as fp:
            payload = json.load(fp)
        registry = URL(config.registry_url).host
        assert payload["credHelpers"] == {registry: "neuro"}
        assert payload["test"] == "value"

    def test_merge_file_with_existing_helpers(self, run_cli, tmp_path: Path, config):
        path = tmp_path / ".docker"
        path.mkdir()
        json_path = path / "config.json"
        with json_path.open("w") as fp:
            json.dump({"test": "value", "credHelpers": {"some.com": "handler"}}, fp)
        capture = run_cli(["config", "docker", "--config", str(path)])
        assert not capture.err
        assert json_path.is_file()
        with json_path.open() as fp:
            payload = json.load(fp)
        registry = URL(config.registry_url).host
        assert payload["credHelpers"] == {registry: "neuro", "some.com": "handler"}
        assert payload["test"] == "value"


class TestHelper:
    def test_no_params_use(self, run_dch):
        capture = run_dch([])
        assert capture.code != EX_OK

    def test_too_mach_params(self, run_dch):
        capture = run_dch(["one", "two"])
        assert capture.code != EX_OK

    def test_unknown_operation(self, run_dch):
        capture = run_dch(["ping"])
        assert capture.code != EX_OK

    def test_store_operation(self, run_dch):
        capture = run_dch(["store"])
        assert capture.code != EX_OK

    def test_anon_get_operation(self, run_dch, monkeypatch, config_anon):
        registry = URL(config_anon.registry_url).host
        monkeypatch.setattr("sys.stdin", io.StringIO(registry))
        capture = run_dch(["get"], True)
        assert capture.code != EX_OK

    def test_unknown_registry_get_operation(self, run_dch, monkeypatch, config):
        registry = "macro.net"
        monkeypatch.setattr("sys.stdin", io.StringIO(registry))
        capture = run_dch(["get"], True)
        assert capture.code != EX_OK

    def test_get_operation(self, run_dch, monkeypatch, config):
        registry = URL(config.registry_url).host
        monkeypatch.setattr("sys.stdin", io.StringIO(registry))
        capture = run_dch(["get"])
        assert capture.code == EX_OK
        payload = json.loads(capture.out)
        assert payload == {"Username": "token", "Secret": config.auth}
