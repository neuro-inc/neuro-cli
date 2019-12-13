import abc
from time import time

import click


TICK_TIMEOUT = 1
CSI = "\033["
CURSOR_UP = f"{CSI}{{}}A"
CURSOR_DOWN = f"{CSI}{{}}B"
CLEAR_LINE_TAIL = f"{CSI}0K"


class AbstractPrinter(abc.ABC):
    """
        Printer is mechanism for displaying some text to end-user
    """

    def close(self) -> str:
        return ""

    @abc.abstractmethod
    def print(self, text: str) -> str:  # pragma: no cover
        pass


class TTYPrinter(AbstractPrinter):
    """
        TTYPrinter allow to output texts in specified bu number lines
        Cursor will be keeped after latest line. Then if exception raised
        error message will be printed after reported before lines
    """

    def __init__(self) -> None:
        self._total_lines = 0

    @property
    def total_lines(self) -> int:
        return self._total_lines

    def print(self, text: str, lineno: int = -1) -> str:
        """
        Print given text on specified line
        If lineno is not passed then text will be printed on latest line
        """
        if lineno < 0:
            lineno = self._total_lines

        lines = text.split("\n")
        commands = []
        diff = self._total_lines - lineno

        if diff > 0:
            commands.append(CURSOR_UP.format(diff))
            for i, line in enumerate(lines):
                commands.append(line)
                if i < diff:
                    commands.append(CLEAR_LINE_TAIL)
                commands.append("\n")
        else:
            if diff < 0:
                commands.append("\n" * (-diff))
                commands.append(CURSOR_UP.format(1))
            commands.append(text)
            commands.append("\n")

        diff -= len(lines)
        if diff > 0:
            commands.append(CURSOR_DOWN.format(diff))
        message = "".join(commands)

        self._total_lines = max(self._total_lines, lineno + len(lines))
        self._print(message)
        return message

    def _print(self, text: str) -> None:
        click.echo(text, nl=False)


class StreamPrinter(AbstractPrinter):
    """
    Print lines ony by one
    Additional tick method for printing simple progress(dots) with spam
    control.
    """

    def __init__(self) -> None:
        self._first = True
        self._last_usage_time = 0.0

    def print(self, text: str) -> str:
        message = ""
        if self._first:
            self._first = False
        else:
            message += "\n"
        message += text
        self._last_usage_time = time()
        self._print(message)
        return message

    def _print(self, text: str) -> None:
        print(text, end="")

    def tick(self) -> str:
        self._first = False
        if time() - self._last_usage_time < TICK_TIMEOUT:
            return ""
        message = "."
        self._last_usage_time = time()
        self._print(message)
        return message

    def close(self) -> str:
        if not self._first:
            self._print("\n")
            return "\n"
        return ""
