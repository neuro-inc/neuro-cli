import inspect
import sys
from pathlib import Path
from typing import Callable, List

import toml

from .conftest import SysCapWithCode
import pytest


_RunCli = Callable[[List[str]], SysCapWithCode]


@pytest.fixture
def script() -> str:
    script = Path(__file__).parent / "script.py"
    return sys.executable + " " + str(script)


def test_internal_alias_simple(run_cli: _RunCli, nmrc_path: Path) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(toml.dumps({"alias": {"user-cmd": {"cmd": "help ls"}}}))
    capture = run_cli(["user-cmd"])
    assert capture.code == 0
    assert 'List directory contents' in capture.out


def test_internal_alias_refers_to_unknown(run_cli: _RunCli, nmrc_path: Path) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(toml.dumps({"alias": {"user-cmd": {"cmd": "unknown command"}}}))
    capture = run_cli(["user-cmd"])
    assert capture.code == 2
    assert 'Error: Alias user-cmd refers to unknown command "unknown"' in capture.err


def test_internal_alias_help(run_cli: _RunCli, nmrc_path: Path) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(toml.dumps({"alias": {"lsl": {"cmd": "storage ls -l"}}}))
    capture = run_cli(["lsl", "--help"])
    assert capture.code == 0
    prog_name = Path(sys.argv[0]).name
    expected = inspect.cleandoc(
        f"""\
        Usage: {prog_name} lsl [OPTIONS]

        Alias for "pytest storage ls -l"

        Options:
          --help  Show this message and exit.
    """
    )
    assert expected == capture.out


def test_internal_alias_help_custom_msg(run_cli: _RunCli, nmrc_path: Path) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "lsl": {
                        "cmd": "storage ls -l",
                        "help": "Custom ls with long output.",
                    }
                }
            }
        )
    )
    capture = run_cli(["lsl", "--help"])
    assert capture.code == 0
    prog_name = Path(sys.argv[0]).name
    expected = inspect.cleandoc(
        f"""\
        Usage: {prog_name} lsl [OPTIONS]

        Alias for "pytest storage ls -l"

        Custom ls with long output.

        Options:
          --help  Show this message and exit.
    """
    )
    assert expected == capture.out


def test_external_alias_no_arg(run_cli: _RunCli, nmrc_path: Path, script: str) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "user-cmd": {
                        "exec": script,
                    }
                }
            }
        )
    )
    capture = run_cli(["user-cmd"])
    assert capture.code == 0
    assert "[]" == capture.out


def test_external_alias_no_arg_help(run_cli: _RunCli, nmrc_path: Path) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "user-cmd": {
                        "exec": "script",
                    }
                }
            }
        )
    )
    capture = run_cli(["user-cmd", "--help"])
    assert capture.code == 0
    prog_name = Path(sys.argv[0]).name
    expected = inspect.cleandoc(
        f"""\
        Usage: {prog_name} user-cmd [OPTIONS]

        Alias for "script"

        Options:
          --help  Show this message and exit.
    """
    )
    assert expected == capture.out


def test_external_alias_arg(run_cli: _RunCli, nmrc_path: Path, script: str) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "user-cmd": {
                        "exec": f"{script} {{arg}}",
                        "args": "ARG",
                    }
                }
            }
        )
    )
    capture = run_cli(["user-cmd", "argument"])
    assert capture.code == 0
    assert "['argument']" == capture.out


def test_external_alias_arg_help(run_cli: _RunCli, nmrc_path: Path) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "user-cmd": {
                        "exec": "script {arg}",
                        "args": "ARG",
                    }
                }
            }
        )
    )
    capture = run_cli(["user-cmd", "--help"])
    assert capture.code == 0
    prog_name = Path(sys.argv[0]).name
    expected = inspect.cleandoc(
        f"""\
        Usage: {prog_name} user-cmd [OPTIONS] ARG

        Alias for "script {{arg}}"

        Options:
          --help  Show this message and exit.
    """
    )
    assert expected == capture.out
