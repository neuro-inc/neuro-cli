import abc
from os import linesep
from time import time
from typing import Optional


TICK_TIMEOUT = 1
CSI = "\033["
CURSOR_UP = f"{CSI}{{}}A"
CURSOR_DOWN = f"{CSI}{{}}B"
CLEAR_LINE_TAIL = f"{CSI}0K"
CURSOR_HOME = f"{CSI}1G"

_ACTIVE_REPORTER_INSTANCE: Optional["Reporter"] = None


class Reporter:
    """
        Reporter allow to print some text
        Only one Reporter can be active at one moment
    """

    def __init__(self) -> None:
        global _ACTIVE_REPORTER_INSTANCE
        if _ACTIVE_REPORTER_INSTANCE:
            raise RuntimeError("Only one Reporter can be active")
        _ACTIVE_REPORTER_INSTANCE = self
        pass

    @property
    def active(self) -> bool:
        global _ACTIVE_REPORTER_INSTANCE
        return _ACTIVE_REPORTER_INSTANCE == self

    def close(self) -> None:
        global _ACTIVE_REPORTER_INSTANCE
        if not self.active:
            raise RuntimeError("Only active Reporter can be closed")
        _ACTIVE_REPORTER_INSTANCE = None
        pass

    @abc.abstractmethod
    def report(self, text: str) -> None:
        pass

    def _escape(self, text: str) -> str:
        return text.translate({10: " ", 13: " "})


class MultilineReporter(Reporter):
    """
        MultilineReporter allow to output texts in specified by nymber lines
        Cursor will be keeped after latest line. Then if exception raised
        error message will be printed after reported before lines
    """

    def __init__(self) -> None:
        super().__init__()
        self._total_lines = 0

    @property
    def total_lines(self) -> int:
        return self._total_lines

    def report(self, text: str, lineno: Optional[int] = None) -> None:
        """
        Print given text on specified line
        If lineno is not passed then  text will be printed on latest line

        """

        assert lineno is None or lineno > 0
        if not self.active:
            raise RuntimeError("Only active Reporter can be used")

        if not lineno:
            lineno = self._total_lines + 1

        commands = []
        diff = self._total_lines - lineno + 1
        if diff > 0:
            commands.append(CURSOR_UP.format(diff))
        elif diff < 0:
            commands.append(linesep * (-1 * diff))
            commands.append(CURSOR_UP.format(1))
        commands.append(self._escape(text) + CLEAR_LINE_TAIL + "\n")
        if diff > 0:
            commands.append(CURSOR_DOWN.format(diff - 1))
        print("".join(commands), end="", flush=True)

        self._total_lines = max(self._total_lines, lineno)


class SingleLineReporter(Reporter):
    """
    All messages will be printed on one line
    """

    def close(self) -> None:
        print(CURSOR_UP.format(1) + CLEAR_LINE_TAIL, flush=True)

    def report(self, text: str) -> None:
        print(CURSOR_UP.format(1) + self._escape(text) + CLEAR_LINE_TAIL, flush=True)


class StreamReporter(Reporter):
    """
    Print lines ony by one
    Additional tick method for printing simple progress(dots) with spam
    control.
    """

    def __init__(self) -> None:
        super().__init__()
        self._tick_mode = False
        self._last_report = 0.0

    def report(self, text: str) -> None:
        if self._tick_mode:
            print()
            self._tick_mode = False
        print(text)
        self._last_report = time()

    def tick(self) -> None:
        if time() - self._last_report < TICK_TIMEOUT:
            return
        print(".", end="", flush=True)
        self._tick_mode = True
        self._last_report = time()
