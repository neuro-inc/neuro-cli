import asyncio
from textwrap import dedent

from neuromation.cli.main import neuro


RC_TEXT = "url: http://platform.dev.neuromation.io/api/v1\n"


def test_help(run):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(asyncio.new_event_loop())

    _, captured = run(["help"], RC_TEXT)
    assert not captured.err
    assert captured.out == neuro.__doc__ + "\n"

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(asyncio.new_event_loop())
    commands = loop.run_until_complete(neuro(None, None, None, None))

    for command, func in commands.items():
        if not hasattr(func, "_command_name"):
            continue

        asyncio.set_event_loop(asyncio.new_event_loop())
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

    _, captured = run(["help", "job", "list", "--status", "pending"], RC_TEXT)
    assert not captured.err
    loop.close()
