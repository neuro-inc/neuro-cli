from textwrap import dedent

import pytest
from click.testing import CliRunner

from neuromation.cli.root import Root
from neuromation.cli.utils import JOB_NAME, DeprecatedGroup, MainGroup, command, group


def test_print() -> None:
    @group()
    def sub_command() -> None:
        pass

    @command()
    async def plain_cmd(root: Root) -> None:
        pass

    @group(cls=MainGroup)
    def main() -> None:
        pass

    main.add_command(sub_command)
    main.add_command(plain_cmd)

    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Usage: main [OPTIONS] COMMAND [ARGS]...

        Commands:
          sub-command

        Command Shortcuts:
          plain-cmd

        Use "neuro help <command>" for more information about a given command or topic.
        Use "neuro --options" for a list of global command-line options (applies to all
        commands).
    """
    )


def test_print_use_group_helpers() -> None:
    @group(cls=MainGroup)
    def main() -> None:
        pass

    @main.group()
    def sub_command() -> None:
        pass

    @main.command()
    async def plain_cmd(root: Root) -> None:
        pass

    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Usage: main [OPTIONS] COMMAND [ARGS]...

        Commands:
          sub-command

        Command Shortcuts:
          plain-cmd

        Use "neuro help <command>" for more information about a given command or topic.
        Use "neuro --options" for a list of global command-line options (applies to all
        commands).
    """
    )


def test_print_hidden() -> None:
    @group()
    def sub_command() -> None:
        pass

    @command(hidden=True)
    async def plain_cmd(root: Root) -> None:
        pass

    @group()
    def main() -> None:
        pass

    main.add_command(sub_command)
    main.add_command(plain_cmd)

    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Usage: main [OPTIONS] COMMAND [ARGS]...

        Commands:
          sub-command
    """
    )


def test_print_deprecated_group() -> None:
    @group()
    def sub_command() -> None:
        """
        Sub-command.
        """

    @group()
    def main() -> None:
        pass

    main.add_command(sub_command)
    main.add_command(DeprecatedGroup(sub_command, name="alias"))

    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Usage: main [OPTIONS] COMMAND [ARGS]...

        Commands:
          sub-command  Sub-command
          alias        Alias for sub-command
    """
    )


def test_print_deprecated_group_content() -> None:
    @group()
    def sub_command() -> None:
        """
        Sub-command.
        """

    @sub_command.command()
    async def cmd(root: Root) -> None:
        """Command.

        Detailed description is here.
        """

    @group(cls=MainGroup)
    def main() -> None:
        pass

    main.add_command(sub_command)
    main.add_command(DeprecatedGroup(sub_command, name="alias"))

    runner = CliRunner()
    result = runner.invoke(main, ["alias"])
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Usage: main alias [OPTIONS] COMMAND [ARGS]...

          Alias for sub-command (DEPRECATED)

        Commands:
          cmd  Command
    """
    )


def test_print_deprecated_no_help() -> None:
    @command(deprecated=True)
    async def main(root: Root) -> None:
        pass

    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Usage: main [OPTIONS]

           (DEPRECATED)

        Options:
          --help  Show this message and exit.
    """
    )


def test_print_deprecated_with_help() -> None:
    @command(deprecated=True)
    async def main(root: Root) -> None:
        """Main help."""

    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Usage: main [OPTIONS]

          Main help. (DEPRECATED)

        Options:
          --help  Show this message and exit.
    """
    )


def test_print_help_with_examples() -> None:
    @command()
    async def main(root: Root) -> None:
        """
        Main help.

        Examples:

        # comment
        example

        """

    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Usage: main [OPTIONS]

          Main help.

        Examples:
          # comment
          example

        Options:
          --help  Show this message and exit.
    """
    )


class TestJobNameType:
    def test_ok(self) -> None:
        name = "a-bc-def"
        assert name == JOB_NAME.convert(name, param=None, ctx=None)

    def test_too_short(self) -> None:
        with pytest.raises(ValueError, match="Invalid job name"):
            JOB_NAME.convert("a" * 2, param=None, ctx=None)

    def test_too_long(self) -> None:
        with pytest.raises(ValueError, match="Invalid job name"):
            JOB_NAME.convert("a" * 41, param=None, ctx=None)

    @pytest.mark.parametrize(
        "name",
        [
            "abc@",  # invalid character
            "abc-DEF",  # capital letters
            "abc--def",  # two consequent hyphens
            "-abc-def",  # hyphen as the first symbol
            "abc-def-",  # hyphen as the last symbol
        ],
    )
    def test_invalid_pattern(self, name: str) -> None:
        with pytest.raises(ValueError, match="Invalid job name"):
            JOB_NAME.convert(name, param=None, ctx=None)
