from textwrap import dedent

from neuromation.cli.main import neuro


RC_TEXT = "url: http://platform.dev.neuromation.io/api/v1\n"


def test_help(run):
    _, captured = run(["help"], RC_TEXT)
    assert not captured.err
    assert captured.out == neuro.__doc__ + "\n"

    commands = neuro(None, None, None, None)

    for command, func in commands.items():
        if not hasattr(func, "_command_name"):
            continue

        # the following commands don't have another
        # command as an argument, hence COMMAND help
        # is not applicable
        if command in ["share"]:
            continue

        _, captured = run([command, "help"], RC_TEXT)
        assert not captured.err
        assert captured.out == dedent(func.__doc__) + "\n"
