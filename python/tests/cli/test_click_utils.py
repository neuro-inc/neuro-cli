from textwrap import dedent

from click.testing import CliRunner

from neuromation.cli.utils import DeprecatedGroup, MainGroup, command, group


def test_print():
    @group()
    def sub_command():
        pass

    @command()
    def plain_cmd():
        pass

    @group(cls=MainGroup)
    def main():
        pass

    main.add_command(sub_command)
    main.add_command(plain_cmd)

    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Usage: main [OPTIONS] COMMAND [ARGS]...

        Options:
          --help  Show this message and exit.

        Command Groups:
          sub-command

        Commands:
          plain-cmd
    """
    )


def test_print_use_group_helpers():
    @group(cls=MainGroup)
    def main():
        pass

    @main.group()
    def sub_command():
        pass

    @main.command()
    def plain_cmd():
        pass

    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Usage: main [OPTIONS] COMMAND [ARGS]...

        Options:
          --help  Show this message and exit.

        Command Groups:
          sub-command

        Commands:
          plain-cmd
    """
    )


def test_print_hidden():
    @group()
    def sub_command():
        pass

    @command(hidden=True)
    def plain_cmd():
        pass

    @group(cls=MainGroup)
    def main():
        pass

    main.add_command(sub_command)
    main.add_command(plain_cmd)

    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Usage: main [OPTIONS] COMMAND [ARGS]...

        Options:
          --help  Show this message and exit.

        Command Groups:
          sub-command
    """
    )


def test_print_deprecated_group():
    @group()
    def sub_command():
        """
        Sub-command.
        """

    @group(cls=MainGroup)
    def main():
        pass

    main.add_command(sub_command)
    main.add_command(DeprecatedGroup(sub_command, name="alias"))

    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Usage: main [OPTIONS] COMMAND [ARGS]...

        Options:
          --help  Show this message and exit.

        Command Groups:
          alias        Alias for sub-command
          sub-command  Sub-command.
    """
    )


def test_print_deprecated_group_content():
    @group()
    def sub_command():
        """
        Sub-command.
        """

    @sub_command.command()
    def cmd():
        """Command."""

    @group(cls=MainGroup)
    def main():
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

        Options:
          --help  Show this message and exit.

        Commands:
          cmd  Command.
    """
    )
