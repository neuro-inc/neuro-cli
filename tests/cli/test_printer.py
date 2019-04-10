from os import linesep
from typing import List

import pytest

from neuromation.cli.printer import StreamPrinter, TTYPrinter


class TestStreamPrinter:
    @pytest.fixture
    def mocked_printer(self, monkeypatch):
        messages: List[str] = []

        def _messages():
            return messages

        def _print(message):
            messages.append(message)

        printer = StreamPrinter()
        monkeypatch.setattr(printer, "_print", _print)
        return [printer, _messages]

    def test_no_messages(self, mocked_printer):
        printer, messages = mocked_printer
        assert messages() == []
        printer.close()
        assert "".join(messages()) == ""

    def test_one_message(self, mocked_printer):
        printer, messages = mocked_printer
        printer.print("message")
        printer.close()
        assert "".join(messages()) == f"message{linesep}"

    def test_two_messages(self, mocked_printer):
        printer, messages = mocked_printer
        printer.print("message1")
        printer.print("message2")
        printer.close()
        assert "".join(messages()) == f"message1{linesep}message2{linesep}"

    def test_ticks_without_messages(self, mocked_printer):
        printer, messages = mocked_printer
        printer.tick()
        printer.close()
        assert "".join(messages()) == f".{linesep}"

    def test_ticks_with_messages(self, mocked_printer, monkeypatch):
        monkeypatch.setattr("neuromation.cli.printer.TICK_TIMEOUT", 0)
        printer, messages = mocked_printer
        printer.tick()
        printer.print("message")
        printer.tick()
        printer.tick()
        printer.close()
        assert "".join(messages()) == f".{linesep}message..{linesep}"

    def test_ticks_spam_control(self, mocked_printer, monkeypatch):
        monkeypatch.setattr("neuromation.cli.printer.TICK_TIMEOUT", 1000)
        printer, messages = mocked_printer
        printer.tick()
        printer.tick()
        printer.close()
        assert "".join(messages()) == f".{linesep}"


class TestTTYPrinter:
    @pytest.fixture
    def mocked_printer(self, monkeypatch):
        messages: List[str] = []

        def _messages():
            return messages

        def _print(message):
            messages.append(message)

        printer = TTYPrinter()
        monkeypatch.setattr(printer, "_print", _print)
        return [printer, _messages]

    def test_no_messages(self, mocked_printer):
        printer, messages = mocked_printer
        assert messages() == []
        printer.close()
        assert "".join(messages()) == ""

    def test_one_message(self, mocked_printer):
        printer, messages = mocked_printer
        printer.print("message")
        printer.close()
        assert "".join(messages()) == f"message{linesep}"

    def test_two_messages(self, mocked_printer):
        printer, messages = mocked_printer
        printer.print("message1")
        printer.print("message2")
        printer.close()
        assert "".join(messages()) == f"message1{linesep}message2{linesep}"

    # very simple test
    def test_message_lineno(self, mocked_printer):
        printer, messages = mocked_printer
        printer.print("message1")
        printer.print("message1-replace", 1)
        printer.print("message3", 3)
        printer.close()
        msgs = "".join(messages())
        assert "message1" in msgs
        assert "message1-replace" in msgs
        assert "message3" in msgs
