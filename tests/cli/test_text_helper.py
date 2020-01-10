import click
import pytest

from neuromation.cli.text_helper import StyledTextHelper


class TestStyledTextHelper:
    @pytest.mark.parametrize(
        "text, expected",
        [("Simple text", False), (click.style("Harder ", bold=True) + "text", True)],
    )
    def test_is_styled(self, text: str, expected: bool) -> None:
        assert StyledTextHelper.is_styled(text) is expected

    @pytest.mark.parametrize(
        "text, expected",
        [("Simple text", 11), (click.style("Harder ", bold=True) + "text", 11)],
    )
    def test_width(self, text: str, expected: int) -> None:
        assert StyledTextHelper.width(text) == expected

    @pytest.mark.parametrize(
        "text, width, expected",
        [
            # Not styled cases
            ("Simple text", 100, "Simple text"),
            ("Simple text", 6, "Simple"),
            # Styled cases
            (
                click.style("Harder ", bold=True) + "text",
                7,
                click.style("Harder ", bold=True),
            ),
            (
                click.style("Harder ", bold=True) + "text",
                9,
                click.style("Harder ", bold=True) + "te",
            ),
            (
                click.style("Harder ", bold=True) + "text",
                4,
                click.style("Hard", bold=True),
            ),
            (
                click.style("Very ", underline=True, bold=True, reset=False)
                + click.style("Hard", bold=True)
                + "text",
                4,
                click.style("Very", underline=True, bold=True),
            ),
            (
                click.style("Very ", underline=True, bold=True, reset=False)
                + click.style("Hard", bold=True)
                + "text",
                8,
                click.style("Very ", underline=True, bold=True, reset=False)
                + click.style("Har", bold=True),
            ),
        ],
    )
    def test_trim(self, text: str, width: int, expected: str) -> None:
        assert StyledTextHelper.trim(text, width) == expected

    @pytest.mark.parametrize(
        "text, width, expected",
        [
            # Not styled cases
            ("Simple text", 100, ["Simple text"]),
            ("Simple text", 6, ["Simple", "text"]),
            ("Simple text", 4, ["Simp", "le", "text"]),
            # Styled cases
            (
                click.style("Harder ", bold=True) + "text",
                100,
                [click.style("Harder ", bold=True) + "text"],
            ),
            (
                click.style("Harder ", bold=True) + "text",
                6,
                [click.style("Harder", bold=True), "text"],
            ),
            (
                click.style("Harder ", bold=True) + "text",
                4,
                [click.style("Hard", bold=True), click.style("er", bold=True), "text"],
            ),
            (
                click.style("Very ", underline=True, reset=False)
                + click.style("Hard", bold=True)
                + " text",
                4,
                [
                    click.style("Very", underline=True),
                    click.style("", underline=True, reset=False)
                    + click.style("Hard", bold=True),
                    "text",
                ],
            ),
        ],
    )
    def test_wrap(self, text: str, width: int, expected: str) -> None:
        assert StyledTextHelper.wrap(text, width) == expected
