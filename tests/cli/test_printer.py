from os import linesep
from typing import Any

import pytest

from neuromation.cli.printer import StreamPrinter, TTYPrinter


class TestStreamPrinter:
    @pytest.fixture
    def printer(self) -> StreamPrinter:
        return StreamPrinter()

    def test_no_messages(self, printer: StreamPrinter, capfd: Any) -> None:
        printer.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ""

    def test_one_message(self, printer: StreamPrinter, capfd: Any) -> None:
        printer.print("message")
        printer.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == f"message{linesep}"

    def test_two_messages(self, printer: StreamPrinter, capfd: Any) -> None:
        printer.print("message1")
        printer.print("message2")
        printer.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == f"message1{linesep}message2{linesep}"

    def test_ticks_without_messages(self, printer: StreamPrinter, capfd: Any) -> None:
        printer.tick()
        printer.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == f".{linesep}"

    def test_ticks_with_messages(
        self, printer: StreamPrinter, capfd: Any, monkeypatch: Any
    ) -> None:
        monkeypatch.setattr("neuromation.cli.printer.TICK_TIMEOUT", 0)
        printer.tick()
        printer.print("message")
        printer.tick()
        printer.tick()
        printer.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == f".{linesep}message..{linesep}"

    def test_ticks_spam_control(
        self, printer: StreamPrinter, capfd: Any, monkeypatch: Any
    ) -> None:
        monkeypatch.setattr("neuromation.cli.printer.TICK_TIMEOUT", 1000)
        printer.tick()
        printer.tick()
        printer.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == f".{linesep}"


class TestTTYPrinter:
    @pytest.fixture
    def printer(self, click_tty_emulation: Any) -> TTYPrinter:
        return TTYPrinter()

    def test_no_messages(self, capfd: Any, printer: TTYPrinter) -> None:
        printer.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ""

    def test_one_message(self, capfd: Any, printer: TTYPrinter) -> None:
        printer.print("message")
        printer.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == f"message{linesep}"

    def test_two_messages(self, capfd: Any, printer: TTYPrinter) -> None:
        printer.print("message1")
        printer.print("message2")
        printer.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == f"message1{linesep}message2{linesep}"

    # very simple test
    def test_message_lineno(self, printer: TTYPrinter, capfd: Any) -> None:
        assert printer.total_lines == 0
        printer.print("message1")
        assert printer.total_lines == 1
        printer.print("message1-replace", 0)
        assert printer.total_lines == 1
        printer.print("message3", 2)
        assert printer.total_lines == 3
        printer.print("message7", 6)
        assert printer.total_lines == 7
        printer.print("message2", 1)
        assert printer.total_lines == 7
        printer.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert "message1" in out
        assert "message1-replace" in out
        assert "message3" in out
        assert "message7" in out
        assert "message2" in out
        CSI = "\033["
        assert CSI in out
        assert f"{CSI}0A" not in out
        assert f"{CSI}0B" not in out
