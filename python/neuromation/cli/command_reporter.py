import abc
from typing import Optional


CSI = "\033["
CURSOR_UP = f"{CSI}{{}}F"
CURSOR_DOWN = f"{CSI}{{}}E"
ERASE_TO_EOL = f"{CSI}K"
CURSOR_HOME = f"{CSI}1G"

_ACTIVE_REPORTER_INSTANCE: Optional["Reporter"] = None


class Reporter:
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


class MultilineReporter(Reporter):
    def __init__(self) -> None:
        super().__init__()
        self.lineno = 0
        self.max_lineno = 0

    def __del__(self) -> None:
        if self.active:
            self.close()

    def close(self) -> None:
        self._goto(self.max_lineno + 1)
        super().close()

    def report(self, text: str, lineno: Optional[int] = None) -> None:
        if not self.active:
            raise RuntimeError("Only active Reporter can be used")
        if lineno is not None:
            self._goto(lineno)
        print(text + ERASE_TO_EOL, end="", flush=True)

    def _goto(self, lineno: int) -> None:
        diff = lineno - self.lineno
        if diff < 0:
            print(CURSOR_UP.format(-1 * diff), end="", flush=True)
        elif diff > 0:
            if lineno > self.max_lineno:
                self._goto(self.max_lineno)
                for _ in range(self.max_lineno, lineno):
                    print(flush=True)
            else:
                print(CURSOR_DOWN.format(diff), end="", flush=True)
        self.lineno = lineno
        self.max_lineno = max(self.max_lineno, lineno)


class SingleLineReporter(Reporter):
    def close(self) -> None:
        print(flush=True)

    def report(self, text: str) -> None:
        print(CURSOR_HOME + text + ERASE_TO_EOL, end="", flush=True)


class QuietReporter(Reporter):
    def report(self, text: str) -> None:
        pass


class StreamReporter(Reporter):
    def report(self, text: str) -> None:
        print(text)
