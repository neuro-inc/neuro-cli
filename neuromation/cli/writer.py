import abc
from os import linesep
from time import time
from typing import Optional

import click


TICK_TIMEOUT = 1
CSI = "\033["
CURSOR_UP = f"{CSI}{{}}A"
CURSOR_DOWN = f"{CSI}{{}}B"
CLEAR_LINE_TAIL = f"{CSI}0K"
CURSOR_HOME = f"{CSI}1G"


class AbstractPrinter(abc.ABC):
    """
        Printer is mechanism for displaying some text to end-user
    """

    def __init__(self, print: bool = False):
        self._print = print

    def close(self) -> str:
        return ""

    @abc.abstractmethod
    def print(self, text: str) -> str:
        pass

    def _escape(self, text: str) -> str:
        return text.translate({10: " ", 13: " "})

    def _process(self, message: str) -> str:
        if self._print:
            click.echo(message, nl=False)
        return message


class TTYPrinter(AbstractPrinter):
    """
        TTYPrinter allow to output texts in specified bu number lines
        Cursor will be keeped after latest line. Then if exception raised
        error message will be printed after reported before lines
    """

    def __init__(self, print: bool = False):
        super().__init__(print)
        self._total_lines = 0

    @property
    def total_lines(self) -> int:
        return self._total_lines

    def print(self, text: str, lineno: Optional[int] = None) -> str:
        """
        Print given text on specified line
        If lineno is not passed then  text will be printed on latest line
        """
        assert lineno is None or lineno > 0
        if not lineno:
            lineno = self._total_lines + 1

        commands = []
        diff = self._total_lines - lineno + 1
        if diff > 0:
            commands.append(CURSOR_UP.format(diff))
        elif diff < 0:
            commands.append(linesep * (-1 * diff))
            commands.append(CURSOR_UP.format(1))
        commands.append(self._escape(text) + CLEAR_LINE_TAIL + linesep)
        if diff > 0:
            commands.append(CURSOR_DOWN.format(diff - 1))
        message = "".join(commands)

        self._total_lines = max(self._total_lines, lineno)
        return self._process(message)


class StreamPrinter(AbstractPrinter):
    """
    Print lines ony by one
    Additional tick method for printing simple progress(dots) with spam
    control.
    """

    def __init__(self, print: bool = False) -> None:
        super().__init__(print)
        self._first = True
        self._last_usage_time = 0.0

    def _process(self, message: str) -> str:
        if self._print:
            print(message, end="")
        return message

    def print(self, text: str) -> str:
        message = ""
        if self._first:
            self._first = False
        else:
            message += linesep
        message += text
        self._last_usage_time = time()
        return self._process(message)

    def tick(self) -> str:
        self._first = False
        if time() - self._last_usage_time < TICK_TIMEOUT:
            return ""
        message = "."
        self._last_usage_time = time()
        return self._process(message)

    def close(self) -> str:
        message = linesep
        return self._process(message)
