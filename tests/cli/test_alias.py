import inspect
import sys
from pathlib import Path
from typing import Callable, List

import pytest
import toml

from neuromation.cli.alias import find_alias, list_aliases
from neuromation.cli.root import Root

from .conftest import SysCapWithCode


_RunCli = Callable[[List[str]], SysCapWithCode]


@pytest.fixture
def script() -> str:
    script = Path(__file__).parent / "script.py"
    return (sys.executable + " " + str(script)).replace("\\", "/")


def test_unknown_command(run_cli: _RunCli) -> None:
    capture = run_cli(["unknown-cmd"])
    assert capture.code == 2
    assert "Usage:" in capture.err


class TestInternalAlias:
    def test_internal_alias_simple(self, run_cli: _RunCli, nmrc_path: Path) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(toml.dumps({"alias": {"user-cmd": {"cmd": "help ls"}}}))
        capture = run_cli(["user-cmd"])
        assert capture.code == 0
        assert "List directory contents" in capture.out

    def test_internal_alias_refers_to_unknown(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps({"alias": {"user-cmd": {"cmd": "unknown command"}}})
        )
        capture = run_cli(["user-cmd"])
        assert capture.code == 2
        assert (
            'Error: Alias user-cmd refers to unknown command "unknown"' in capture.err
        )

    def test_internal_alias_help(self, run_cli: _RunCli, nmrc_path: Path) -> None:
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

    def test_internal_alias_help_custom_msg(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
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

    async def test_internal_alias_short_help(self, root: Root, nmrc_path: Path) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(toml.dumps({"alias": {"lsl": {"cmd": "storage ls -l"}}}))
        cmd = await find_alias(root, "lsl")
        assert cmd is not None
        assert cmd.get_short_help_str() == "neuro storage ls -l"

    async def test_internal_alias_short_help_custom_msg(
        self, root: Root, nmrc_path: Path
    ) -> None:
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
        cmd = await find_alias(root, "lsl")
        assert cmd is not None
        assert cmd.get_short_help_str() == "Custom ls with long output."


class TestExternalAliasArgs:
    def test_external_alias_no_arg(
        self, run_cli: _RunCli, nmrc_path: Path, script: str
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(toml.dumps({"alias": {"user-cmd": {"exec": script}}}))
        capture = run_cli(["user-cmd"])
        assert capture.code == 0
        assert "[]" == capture.out

    def test_external_alias_no_arg_help(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
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
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {"alias": {"user-cmd": {"exec": "script", "help": "Custom help."}}}
            )
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

    async def test_external_alias_short_help(self, root: Root, nmrc_path: Path) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(toml.dumps({"alias": {"user-cmd": {"exec": "script"}}}))
        cmd = await find_alias(root, "user-cmd")
        assert cmd is not None
        assert cmd.get_short_help_str() == "script"

    async def test_external_alias_short_help_custom_msg(
        self, root: Root, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {"alias": {"user-cmd": {"exec": "script", "help": "Custom help."}}}
            )
        )
        cmd = await find_alias(root, "user-cmd")
        assert cmd is not None
        assert cmd.get_short_help_str() == "Custom help."

    def test_external_alias_arg(
        self, run_cli: _RunCli, nmrc_path: Path, script: str
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {"alias": {"user-cmd": {"exec": f"{script} {{arg}}", "args": "ARG"}}}
            )
        )
        capture = run_cli(["user-cmd", "argument"])
        assert capture.code == 0
        assert "['argument']" == capture.out

    def test_external_alias_arg_help(self, run_cli: _RunCli, nmrc_path: Path) -> None:
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

    def test_external_alias_arg_help_fix_casing(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps({"alias": {"user-cmd": {"exec": "script {arg}", "args": "Arg"}}})
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
        self, run_cli: _RunCli, nmrc_path: Path, script: str
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

    def test_external_alias_two_arg2_help(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {
                    "alias": {
                        "user-cmd": {
                            "exec": "script {arg1} {arg2}",
                            "args": "ARG1 ARG2",
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
            Usage: {prog_name} user-cmd [OPTIONS] ARG1 ARG2

            Alias for "script {{arg1}} {{arg2}}"

            Options:
              --help  Show this message and exit.
        """
        )
        assert expected == capture.out

    def test_external_alias_optional_arg_provided(
        self, run_cli: _RunCli, nmrc_path: Path, script: str
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
        self, run_cli: _RunCli, nmrc_path: Path, script: str
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

    def test_external_alias_optional_arg_help(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {"alias": {"user-cmd": {"exec": "script {arg}", "args": "[ARG]"}}}
            )
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
        self, run_cli: _RunCli, nmrc_path: Path, script: str
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

    def test_external_alias_multiple_arg_help(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {"alias": {"user-cmd": {"exec": "script {arg}", "args": "ARG..."}}}
            )
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
        self, run_cli: _RunCli, nmrc_path: Path, script: str
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {
                    "alias": {
                        "user-cmd": {"exec": f"{script} {{arg}}", "args": "[ARG]..."}
                    }
                }
            )
        )
        capture = run_cli(["user-cmd", "arg1", "arg2"])
        assert capture.code == 0
        assert "['arg1', 'arg2']" == capture.out

    def test_external_alias_optional_multiple_arg_missed(
        self, run_cli: _RunCli, nmrc_path: Path, script: str
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {
                    "alias": {
                        "user-cmd": {"exec": f"{script} {{arg}}", "args": "[ARG]..."}
                    }
                }
            )
        )
        capture = run_cli(["user-cmd"])
        assert capture.code == 0
        assert "[]" == capture.out

    def test_external_alias_optional_multiple_arg_help(
        self, run_cli: _RunCli, nmrc_path: Path
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

    def test_external_alias_three_args_regular_multiple_optional_help(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {
                    "alias": {
                        "user-cmd": {
                            "exec": "script {arg1} {arg2} {arg3}",
                            "args": "ARG1 ARG2... [ARG3]",
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
            Usage: {prog_name} user-cmd [OPTIONS] ARG1 ARG2... [ARG3]

            Alias for "script {{arg1}} {{arg2}} {{arg3}}"

            Options:
              --help  Show this message and exit.
        """
        )
        assert expected == capture.out


class TestExternalAliasOptions:
    def test_external_alias_option_flag_help_without_help_str(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {"alias": {"user-cmd": {"exec": "script {opt}", "options": ["--opt"]}}}
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
        self, run_cli: _RunCli, nmrc_path: Path
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
        self, run_cli: _RunCli, nmrc_path: Path
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
        self, run_cli: _RunCli, nmrc_path: Path
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

    def test_external_alias_option_metaval_lowercased(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {
                    "alias": {
                        "user-cmd": {
                            "exec": "script {opt}",
                            "options": ["-o, --opt val  Description."],
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
              -o, --opt VAL  Description.
              --help         Show this message and exit.
        """
        )
        assert expected == capture.out

    def test_external_alias_option_short_long_help_with_help_str_inversed_order(
        self, run_cli: _RunCli, nmrc_path: Path
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
        self, run_cli: _RunCli, nmrc_path: Path, script: str
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {
                    "alias": {
                        "user-cmd": {
                            "exec": f"{script} {{opt}}",
                            "options": ["-o, --opt"],
                        }
                    }
                }
            )
        )
        capture = run_cli(["user-cmd", "-o"])
        assert capture.code == 0, capture
        assert capture.out == "['--opt']"

    def test_external_alias_option_call_flag_long(
        self, run_cli: _RunCli, nmrc_path: Path, script: str
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {
                    "alias": {
                        "user-cmd": {
                            "exec": f"{script} {{opt}}",
                            "options": ["-o, --opt"],
                        }
                    }
                }
            )
        )
        capture = run_cli(["user-cmd", "--opt"])
        assert capture.code == 0, capture
        assert capture.out == "['--opt']"

    def test_external_alias_option_call_flag_unset(
        self, run_cli: _RunCli, nmrc_path: Path, script: str
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {
                    "alias": {
                        "user-cmd": {
                            "exec": f"{script} {{opt}}",
                            "options": ["-o, --opt"],
                        }
                    }
                }
            )
        )
        capture = run_cli(["user-cmd"])
        assert capture.code == 0, capture
        assert capture.out == "[]"

    def test_external_alias_option_call_value(
        self, run_cli: _RunCli, nmrc_path: Path, script: str
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

    def test_external_alias_option_call_value_multiple(
        self, run_cli: _RunCli, nmrc_path: Path, script: str
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
        capture = run_cli(["user-cmd", "--opt", "arg1", "--opt", "arg2"])
        assert capture.code == 0, capture
        assert capture.out == "['--opt', 'arg1', '--opt', 'arg2']"

    def test_external_alias_option_call_flag_multiple(
        self, run_cli: _RunCli, nmrc_path: Path, script: str
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {
                    "alias": {
                        "user-cmd": {
                            "exec": f"{script} {{verbose}}",
                            "options": ["-v, --verbose"],
                        }
                    }
                }
            )
        )
        capture = run_cli(["user-cmd", "-vvv"])
        assert capture.code == 0, capture
        assert capture.out == "['--verbose', '--verbose', '--verbose']"


def test_external_alias_exitcode(
    run_cli: _RunCli, nmrc_path: Path, script: str
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "user-cmd": {
                        "exec": f"{script} {{exit}}",
                        "options": ["--exit CODE"],
                    }
                }
            }
        )
    )
    capture = run_cli(["user-cmd", "--exit=10"])
    assert capture.code == 10, capture
    assert capture.out == "['--exit', '10']"


class TestExternalAliasParseErrors:
    def test_external_alias_long_option_not_identifier(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {"alias": {"user-cmd": {"exec": "script {opt}", "options": ["--123"]}}}
            )
        )
        capture = run_cli(["user-cmd", "--opt", "arg"])
        assert capture.code == 70, capture
        assert capture.err.startswith("Cannot parse option --123")

    def test_external_alias_short_option_not_identifier(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {"alias": {"user-cmd": {"exec": "script {opt}", "options": ["-1"]}}}
            )
        )
        capture = run_cli(["user-cmd", "--opt", "arg"])
        assert capture.code == 70, capture
        assert capture.err.startswith("Cannot parse option -1")

    def test_external_alias_option_meta_not_identifier(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {
                    "alias": {
                        "user-cmd": {"exec": "script {opt}", "options": ["--opt 123"]}
                    }
                }
            )
        )
        capture = run_cli(["user-cmd", "--opt", "arg"])
        assert capture.code == 70, capture
        assert capture.err.startswith("Cannot parse option --opt 123")

    def test_external_alias_empty_substitution(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(toml.dumps({"alias": {"user-cmd": {"exec": "script {}"}}}))
        capture = run_cli(["user-cmd"])
        assert capture.code == 70, capture
        assert capture.err.startswith("Empty substitution is not allowed")

    def test_external_alias_uppercased_parameter(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps({"alias": {"user-cmd": {"exec": "script {PARAM}"}}})
        )
        capture = run_cli(["user-cmd"])
        assert capture.code == 70, capture
        assert capture.err.startswith("Parameter PARAM should be lowercased")

    def test_external_alias_invalid_parameter_name(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps({"alias": {"user-cmd": {"exec": "script {123}"}}})
        )
        capture = run_cli(["user-cmd"])
        assert capture.code == 70, capture
        assert capture.err.startswith("Parameter 123 is not a valid identifier")

    def test_external_alias_unknown_parameter(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {
                    "alias": {
                        "user-cmd": {
                            "exec": "script {param}",
                            "options": ["-v, --verbose"],
                        }
                    }
                }
            )
        )
        capture = run_cli(["user-cmd"])
        assert capture.code == 70, capture
        assert capture.err.startswith('Unknown parameter param in "script {param}"')

    def test_external_alias_overlapped_args_and_options(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {
                    "alias": {
                        "user-cmd": {
                            "exec": "script {param}",
                            "options": ["--param"],
                            "args": "PARAM",
                        }
                    }
                }
            )
        )
        capture = run_cli(["user-cmd"])
        assert capture.code == 70, capture
        assert capture.err.startswith(
            "The following names are present in both positional "
            "and optional arguments: param"
        )

    def test_external_alias_nested_args_brackets(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {"alias": {"user-cmd": {"exec": "script {arg}", "args": "[[ARG]]"}}}
            )
        )
        capture = run_cli(["user-cmd"])
        assert capture.code == 70, capture
        assert capture.err.startswith('Nested brackets in "[[ARG]]"')

    def test_external_alias_missing_open_bracket(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {"alias": {"user-cmd": {"exec": "script {arg}", "args": "ARG]"}}}
            )
        )
        capture = run_cli(["user-cmd"])
        assert capture.code == 70, capture
        assert capture.err.startswith('Missing open bracket in "ARG]"')

    def test_external_alias_missing_argument_inside_brackets(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps({"alias": {"user-cmd": {"exec": "script {arg}", "args": "[]"}}})
        )
        capture = run_cli(["user-cmd"])
        assert capture.code == 70, capture
        assert capture.err.startswith('Missing argument inside brackets in "[]"')

    def test_external_alias_ellipsis_should_follow_arg(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps({"alias": {"user-cmd": {"exec": "script {arg}", "args": "..."}}})
        )
        capture = run_cli(["user-cmd"])
        assert capture.code == 70, capture
        assert capture.err.startswith(
            'Ellipsis (...) should follow an argument in "..."'
        )

    def test_external_alias_ellipsis_inside_brackets(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {"alias": {"user-cmd": {"exec": "script {arg}", "args": "[ARG...]"}}}
            )
        )
        capture = run_cli(["user-cmd"])
        assert capture.code == 70, capture
        assert capture.err.startswith('Ellipsis (...) inside of brackets in "[ARG...]"')

    def test_external_alias_successive_ellipsis(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {"alias": {"user-cmd": {"exec": "script {arg}", "args": "ARG......"}}}
            )
        )
        capture = run_cli(["user-cmd"])
        assert capture.code == 70, capture
        assert capture.err.startswith('Successive ellipsis (...) in "ARG......"')

    def test_external_alias_missing_close_bracket1(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {"alias": {"user-cmd": {"exec": "script {arg}", "args": "[ARG"}}}
            )
        )
        capture = run_cli(["user-cmd"])
        assert capture.code == 70, capture
        assert capture.err.startswith('Missing close bracket in "[ARG"')

    def test_external_alias_missing_close_bracket2(
        self, run_cli: _RunCli, nmrc_path: Path
    ) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {"alias": {"user-cmd": {"exec": "script {arg}", "args": "[ARG1 ARG2"}}}
            )
        )
        capture = run_cli(["user-cmd"])
        assert capture.code == 70, capture
        assert capture.err.startswith('Missing close bracket in "[ARG1 ARG2"')


def test_external_alias_simplified(
    run_cli: _RunCli, nmrc_path: Path, script: str
) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "user-cmd": {
                        "exec": f"{script}",
                        "args": "[ARG]...",
                        "options": ["-o, --opt  Option"],
                    }
                }
            }
        )
    )
    capture = run_cli(["user-cmd", "-o", "arg"])
    assert capture.code == 0
    assert "['--opt', 'arg']" == capture.out


async def test_list_aliases(root: Root, nmrc_path: Path) -> None:
    user_cfg = nmrc_path / "user.toml"
    user_cfg.write_text(
        toml.dumps(
            {
                "alias": {
                    "lsl": {
                        "cmd": "storage ls -l",
                        "help": "Custom ls with long output.",
                    },
                    "user-cmd": {"exec": "script"},
                }
            }
        )
    )
    lst = await list_aliases(root)
    names = [cmd.name for cmd in lst]
    assert names == ["lsl", "user-cmd"]


async def test_find_alias_without_config(tmp_path: Path) -> None:
    root = Root(
        color=False,
        tty=False,
        terminal_size=(80, 24),
        disable_pypi_version_check=True,
        network_timeout=60,
        config_path=tmp_path,
        verbosity=0,
        trace=False,
        trace_hide_token=True,
        command_path="",
        command_params=[],
        skip_gmp_stats=True,
    )
    assert await find_alias(root, "unknown-cmd") is None
