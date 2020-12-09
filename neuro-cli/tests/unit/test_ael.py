from prompt_toolkit.key_binding import KeyPress
from prompt_toolkit.keys import Keys

from neuro_cli.ael import _has_detach


def test_detach_short() -> None:
    term = (Keys.ControlP, Keys.ControlQ)
    assert not _has_detach([], term)


def test_detach_not_present() -> None:
    term = (Keys.ControlP, Keys.ControlQ)
    assert not _has_detach(
        [
            KeyPress(Keys.Control0, ""),
            KeyPress(Keys.ControlP, ""),
            KeyPress(Keys.Control1, ""),
        ],
        term,
    )


def test_detach_with_other_symbols() -> None:
    term = (Keys.ControlP, Keys.ControlQ)
    assert not _has_detach(
        [
            KeyPress(Keys.Control0, ""),
            KeyPress(Keys.ControlP, ""),
            KeyPress(Keys.Control1, ""),
            KeyPress(Keys.ControlQ, ""),
        ],
        term,
    )


def test_detach_reversed() -> None:
    term = (Keys.ControlP, Keys.ControlQ)
    assert not _has_detach(
        [
            KeyPress(Keys.Control0, ""),
            KeyPress(Keys.ControlQ, ""),
            KeyPress(Keys.ControlP, ""),
            KeyPress(Keys.Control1, ""),
        ],
        term,
    )


def test_detach_present_at_the_end() -> None:
    term = (Keys.ControlP, Keys.ControlQ)
    assert _has_detach(
        [
            KeyPress(Keys.Control0, ""),
            KeyPress(Keys.ControlP, ""),
            KeyPress(Keys.ControlQ, ""),
        ],
        term,
    )


def test_detach_present_in_the_middle() -> None:
    term = (Keys.ControlP, Keys.ControlQ)
    assert _has_detach(
        [
            KeyPress(Keys.Control0, ""),
            KeyPress(Keys.ControlP, ""),
            KeyPress(Keys.ControlQ, ""),
            KeyPress(Keys.Control1, ""),
        ],
        term,
    )
