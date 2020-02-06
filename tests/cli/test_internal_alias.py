import inspect
import sys
from pathlib import Path
from typing import Callable, List

import toml

from .conftest import SysCapWithCode


_RunCli = Callable[[List[str]], SysCapWithCode]


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
