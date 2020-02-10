import inspect
import sys
from pathlib import Path
from typing import Callable, List

import pytest
import toml

from .conftest import SysCapWithCode


_RunCli = Callable[[List[str]], SysCapWithCode]


@pytest.fixture
def script() -> str:
    script = Path(__file__).parent / "script.py"
    return sys.executable + " " + str(script)


def test_unknown_command(run_cli: _RunCli) -> None:
    capture = run_cli(["unknown-cmd"])
    assert capture.code == 2
    assert "Usage:" in capture.err


def test_internal_alias_simple(run_cli: _RunCli, nmrc_path: Path) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(toml.dumps({"alias": {"user-cmd": {"cmd": "help ls"}}}))
    capture = run_cli(["user-cmd"])
    assert capture.code == 0
    assert "List directory contents" in capture.out


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
    user_cfg.write_text(toml.dumps({"alias": {"user-cmd": {"exec": script}}}))
    capture = run_cli(["user-cmd"])
    assert capture.code == 0
    assert "[]" == capture.out


def test_external_alias_no_arg_help(run_cli: _RunCli, nmrc_path: Path) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(toml.dumps({"alias": {"user-cmd": {"exec": "script"}}}))
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


def test_external_alias_no_arg_help_custom_msg(
    run_cli: _RunCli, nmrc_path: Path
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps({"alias": {"user-cmd": {"exec": "script", "help": "Custom help."}}})
    )
    capture = run_cli(["user-cmd", "--help"])
    assert capture.code == 0
    prog_name = Path(sys.argv[0]).name
    expected = inspect.cleandoc(
        f"""\
        Usage: {prog_name} user-cmd [OPTIONS]

        Alias for "script"

        Custom help.

        Options:
          --help  Show this message and exit.
    """
    )
    assert expected == capture.out


def test_external_alias_arg(run_cli: _RunCli, nmrc_path: Path, script: str) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {"alias": {"user-cmd": {"exec": f"{script} {{arg}}", "args": "ARG"}}}
        )
    )
    capture = run_cli(["user-cmd", "argument"])
    assert capture.code == 0
    assert "['argument']" == capture.out


def test_external_alias_arg_help(run_cli: _RunCli, nmrc_path: Path) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps({"alias": {"user-cmd": {"exec": "script {arg}", "args": "ARG"}}})
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


def test_external_alias_two_arg2(
    run_cli: _RunCli, nmrc_path: Path, script: str
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "user-cmd": {
                        "exec": f"{script} {{arg1}} {{arg2}}",
                        "args": "ARG1 ARG2",
                    }
                }
            }
        )
    )
    capture = run_cli(["user-cmd", "arg1", "arg2"])
    assert capture.code == 0
    assert "['arg1', 'arg2']" == capture.out


def test_external_alias_two_arg2_help(run_cli: _RunCli, nmrc_path: Path) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "user-cmd": {"exec": "script {arg1} {arg2}", "args": "ARG1 ARG2"}
                }
            }
        )
    )
    capture = run_cli(["user-cmd", "--help"])
    assert capture.code == 0
    prog_name = Path(sys.argv[0]).name
    expected = inspect.cleandoc(
        f"""\
        Usage: {prog_name} user-cmd [OPTIONS] ARG1 ARG2

        Alias for "script {{arg1}} {{arg2}}"

        Options:
          --help  Show this message and exit.
    """
    )
    assert expected == capture.out


def test_external_alias_optional_arg_provided(
    run_cli: _RunCli, nmrc_path: Path, script: str
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {"alias": {"user-cmd": {"exec": f"{script} {{arg}}", "args": "[ARG]"}}}
        )
    )
    capture = run_cli(["user-cmd", "argument"])
    assert capture.code == 0
    assert "['argument']" == capture.out


def test_external_alias_optional_arg_missed(
    run_cli: _RunCli, nmrc_path: Path, script: str
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {"alias": {"user-cmd": {"exec": f"{script} {{arg}}", "args": "[ARG]"}}}
        )
    )
    capture = run_cli(["user-cmd"])
    assert capture.code == 0
    assert "[]" == capture.out


def test_external_alias_optional_arg_help(run_cli: _RunCli, nmrc_path: Path) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps({"alias": {"user-cmd": {"exec": "script {arg}", "args": "[ARG]"}}})
    )
    capture = run_cli(["user-cmd", "--help"])
    assert capture.code == 0
    prog_name = Path(sys.argv[0]).name
    expected = inspect.cleandoc(
        f"""\
        Usage: {prog_name} user-cmd [OPTIONS] [ARG]

        Alias for "script {{arg}}"

        Options:
          --help  Show this message and exit.
    """
    )
    assert expected == capture.out


def test_external_alias_multiple_arg_provided(
    run_cli: _RunCli, nmrc_path: Path, script: str
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {"alias": {"user-cmd": {"exec": f"{script} {{arg}}", "args": "ARG..."}}}
        )
    )
    capture = run_cli(["user-cmd", "arg1", "arg2"])
    assert capture.code == 0
    assert "['arg1', 'arg2']" == capture.out


def test_external_alias_multiple_arg_help(run_cli: _RunCli, nmrc_path: Path) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps({"alias": {"user-cmd": {"exec": "script {arg}", "args": "ARG..."}}})
    )
    capture = run_cli(["user-cmd", "--help"])
    assert capture.code == 0
    prog_name = Path(sys.argv[0]).name
    expected = inspect.cleandoc(
        f"""\
        Usage: {prog_name} user-cmd [OPTIONS] ARG...

        Alias for "script {{arg}}"

        Options:
          --help  Show this message and exit.
    """
    )
    assert expected == capture.out


def test_external_alias_optional_multiple_arg_provided(
    run_cli: _RunCli, nmrc_path: Path, script: str
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {"alias": {"user-cmd": {"exec": f"{script} {{arg}}", "args": "[ARG]..."}}}
        )
    )
    capture = run_cli(["user-cmd", "arg1", "arg2"])
    assert capture.code == 0
    assert "['arg1', 'arg2']" == capture.out


def test_external_alias_optional_multiple_arg_missed(
    run_cli: _RunCli, nmrc_path: Path, script: str
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {"alias": {"user-cmd": {"exec": f"{script} {{arg}}", "args": "[ARG]..."}}}
        )
    )
    capture = run_cli(["user-cmd"])
    assert capture.code == 0
    assert "[]" == capture.out


def test_external_alias_optional_multiple_arg_help(
    run_cli: _RunCli, nmrc_path: Path
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {"alias": {"user-cmd": {"exec": "script {arg}", "args": "[ARG]..."}}}
        )
    )
    capture = run_cli(["user-cmd", "--help"])
    assert capture.code == 0
    prog_name = Path(sys.argv[0]).name
    expected = inspect.cleandoc(
        f"""\
        Usage: {prog_name} user-cmd [OPTIONS] [ARG]...

        Alias for "script {{arg}}"

        Options:
          --help  Show this message and exit.
    """
    )
    assert expected == capture.out


def test_external_alias_three_args_optional_multiple_regular_help(
    run_cli: _RunCli, nmrc_path: Path
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "user-cmd": {
                        "exec": "script {arg1} {arg2} {arg3}",
                        "args": "[ARG1] ARG2... ARG3",
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
        Usage: {prog_name} user-cmd [OPTIONS] [ARG1] ARG2... ARG3

        Alias for "script {{arg1}} {{arg2}} {{arg3}}"

        Options:
          --help  Show this message and exit.
    """
    )
    assert expected == capture.out


def test_external_alias_option_flag_help_without_help_str(
    run_cli: _RunCli, nmrc_path: Path
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {"alias": {"user-cmd": {"exec": "script {opt}", "options": ["--opt"],}}}
        )
    )
    capture = run_cli(["user-cmd", "--help"])
    assert capture.code == 0
    prog_name = Path(sys.argv[0]).name
    expected = inspect.cleandoc(
        f"""\
        Usage: {prog_name} user-cmd [OPTIONS]

        Alias for "script {{opt}}"

        Options:
          --opt
          --help  Show this message and exit.
    """
    )
    assert expected == capture.out


def test_external_alias_option_flag_help_with_help_str(
    run_cli: _RunCli, nmrc_path: Path
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "user-cmd": {
                        "exec": "script {opt}",
                        "options": ["--opt  Option description."],
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

        Alias for "script {{opt}}"

        Options:
          --opt   Option description.
          --help  Show this message and exit.
    """
    )
    assert expected == capture.out


def test_external_alias_option_flag_short_long_help_with_help_str(
    run_cli: _RunCli, nmrc_path: Path
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "user-cmd": {
                        "exec": "script {opt}",
                        "options": ["-o, --opt  Option description."],
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

        Alias for "script {{opt}}"

        Options:
          -o, --opt  Option description.
          --help     Show this message and exit.
    """
    )
    assert expected == capture.out


def test_external_alias_option_short_long_help_with_help_str(
    run_cli: _RunCli, nmrc_path: Path
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "user-cmd": {
                        "exec": "script {opt}",
                        "options": ["-o, --opt VAL  Option description."],
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

        Alias for "script {{opt}}"

        Options:
          -o, --opt VAL  Option description.
          --help         Show this message and exit.
    """
    )
    assert expected == capture.out


def test_external_alias_option_short_long_help_with_help_str_inversed_order(
    run_cli: _RunCli, nmrc_path: Path
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "user-cmd": {
                        "exec": "script {opt}",
                        "options": ["--opt, -o VAL  Option description."],
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

        Alias for "script {{opt}}"

        Options:
          -o, --opt VAL  Option description.
          --help         Show this message and exit.
    """
    )
    assert expected == capture.out


def test_external_alias_option_call_flag_short(
    run_cli: _RunCli, nmrc_path: Path, script: str
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "user-cmd": {"exec": f"{script} {{opt}}", "options": ["-o, --opt"],}
                }
            }
        )
    )
    capture = run_cli(["user-cmd", "-o"])
    assert capture.code == 0, capture
    assert capture.out == "['--opt']"


def test_external_alias_option_call_flag_long(
    run_cli: _RunCli, nmrc_path: Path, script: str
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "user-cmd": {"exec": f"{script} {{opt}}", "options": ["-o, --opt"],}
                }
            }
        )
    )
    capture = run_cli(["user-cmd", "--opt"])
    assert capture.code == 0, capture
    assert capture.out == "['--opt']"


def test_external_alias_option_call_flag_unset(
    run_cli: _RunCli, nmrc_path: Path, script: str
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "user-cmd": {"exec": f"{script} {{opt}}", "options": ["-o, --opt"],}
                }
            }
        )
    )
    capture = run_cli(["user-cmd"])
    assert capture.code == 0, capture
    assert capture.out == "[]"


def test_external_alias_option_call_value(
    run_cli: _RunCli, nmrc_path: Path, script: str
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "user-cmd": {
                        "exec": f"{script} {{opt}}",
                        "options": ["-o, --opt VAL"],
                    }
                }
            }
        )
    )
    capture = run_cli(["user-cmd", "--opt", "arg"])
    assert capture.code == 0, capture
    assert capture.out == "['--opt', 'arg']"
