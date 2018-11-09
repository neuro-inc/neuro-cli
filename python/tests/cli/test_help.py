from textwrap import dedent

import pytest

from neuromation.cli.main import neuro


RC_TEXT = "url: http://platform.dev.neuromation.io/api/v1\n" "auth: abc"


def test_help(run):
    _, captured = run(["help"], RC_TEXT)
    assert not captured.err
    assert captured.out == neuro.__doc__ + "\n"

    commands = neuro(None, None, None, None)

    for command, func in commands.items():
        if not hasattr(func, "_command_name"):
            continue

        _, captured = run(["help", command], RC_TEXT)
        assert not captured.err
        assert captured.out == dedent(func.__doc__) + "\n"

    with pytest.raises(SystemExit) as captured:
        run(["help", "mississippi"], RC_TEXT)
    assert captured.type == SystemExit
    assert captured.value.code == 127

    with pytest.raises(SystemExit) as captured:
        run(["help", "--mississippi"], RC_TEXT)
    assert captured.type == SystemExit
    assert captured.value.code == 127

    _, captured = run(["help", "job", "list",
                       "--status", "pending"],
                      RC_TEXT)
    assert not captured.err
