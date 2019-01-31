import click
from neuromation.cli.main import MainGroup
from click.testing import CliRunner
from textwrap import dedent


def test_print():

    @click.group()
    def sub_command():
        pass

    @click.command()
    def plain_cmd():
        pass

    @click.group(cls=MainGroup)
    def main():
        pass

    main.add_command(sub_command)
    main.add_command(plain_cmd)

    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert result.output == dedent("""\
        Usage: main [OPTIONS] COMMAND [ARGS]...

        Options:
          --help  Show this message and exit.

        Command Groups:
          sub-command

        Commands:
          plain-cmd
    """)
