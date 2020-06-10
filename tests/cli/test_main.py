import shutil
from pathlib import Path
from typing import Any, Callable, List

from neuromation.cli.utils import NEURO_STEAL_CONFIG

from .conftest import SysCapWithCode


_RunCli = Callable[[List[str]], SysCapWithCode]


def test_steal_config(
    nmrc_path: Path, run_cli: _RunCli, tmp_path: Path, monkeypatch: Any
) -> None:
    folder = shutil.move(nmrc_path, tmp_path / "orig-cfg")  # type: ignore
    monkeypatch.setenv(NEURO_STEAL_CONFIG, str(folder))
    ret = run_cli(["--neuromation-config", str(tmp_path / ".neuro"), "config", "show"])
    assert ret.code == 0, ret


def test_steal_config_dont_override_existing(
    nmrc_path: Path, run_cli: _RunCli, tmp_path: Path, monkeypatch: Any
) -> None:
    folder = shutil.copytree(nmrc_path, tmp_path / "orig-cfg")
    monkeypatch.setenv(NEURO_STEAL_CONFIG, str(folder))
    ret = run_cli(["--neuromation-config", str(nmrc_path), "config", "show"])
    # FileExistsError
    assert ret.code == 74, ret
    assert "FileExistsError" in ret.err
