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
        assert out == "message\n"

    def test_two_messages(self, printer: StreamPrinter, capfd: Any) -> None:
        printer.print("message1")
        printer.print("message2")
        printer.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == "message1\nmessage2\n"

    def test_ticks_without_messages(self, printer: StreamPrinter, capfd: Any) -> None:
        printer.tick()
        printer.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ".\n"

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
        assert out == ".\nmessage..\n"

    def test_ticks_spam_control(
        self, printer: StreamPrinter, capfd: Any, monkeypatch: Any
    ) -> None:
        monkeypatch.setattr("neuromation.cli.printer.TICK_TIMEOUT", 1000)
        printer.tick()
        printer.tick()
        printer.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ".\n"


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
        assert out == "message\n"

    def test_two_messages(self, capfd: Any, printer: TTYPrinter) -> None:
        printer.print("message1")
        printer.print("message2")
        printer.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == "message1\nmessage2\n"

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

    def test_multiline(self, printer: TTYPrinter, capfd: Any) -> None:
        CSI = "\033["
        assert printer.total_lines == 0
        res = printer.print("message1\nmessage2")
        assert printer.total_lines == 2
        assert res == "message1\nmessage2\n"

        res = printer.print("message3\nmessage4", 1)
        assert printer.total_lines == 3
        assert res == f"{CSI}1Amessage3{CSI}0K\nmessage4\n"

        res = printer.print("message5\nmessage6", 10)
        assert printer.total_lines == 12
        assert res == f"\n\n\n\n\n\n\n{CSI}1Amessage5\nmessage6\n"

        res = printer.print("message7\nmessage8", 5)
        assert printer.total_lines == 12
        assert res == f"{CSI}7Amessage7{CSI}0K\nmessage8{CSI}0K\n{CSI}5B"
