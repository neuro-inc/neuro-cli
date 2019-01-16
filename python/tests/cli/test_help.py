import pytest

from neuromation.cli.commands import help_format
from neuromation.cli.defaults import DEFAULTS
from neuromation.cli.main import neuro


RC_TEXT = "url: http://platform.dev.neuromation.io/api/v1\n"


def test_help(run):
    format_spec = DEFAULTS.copy()

    _, captured = run(["help"], RC_TEXT)
    assert not captured.err
    assert captured.out == help_format(neuro.__doc__, format_spec) + "\n"

    commands = neuro(None, None, None, None, None)

    for command, func in commands.items():
        if not hasattr(func, "_command_name"):
            continue

        _, captured = run(["help", command], RC_TEXT)
        assert not captured.err
        assert captured.out == help_format(func.__doc__, format_spec) + "\n"

    with pytest.raises(SystemExit) as captured:
        run(["help", "mississippi"], RC_TEXT)
    assert captured.type == SystemExit
    assert captured.value.code == 127

    with pytest.raises(SystemExit) as captured:
        run(["help", "--mississippi"], RC_TEXT)
    assert captured.type == SystemExit
    assert captured.value.code == 127

    _, captured = run(["help", "job", "list", "--status", "pending"], RC_TEXT)
    assert not captured.err
