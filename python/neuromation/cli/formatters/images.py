from typing import Dict, Optional

from neuromation.cli.command_reporter import MultilineReporter, StreamReporter
from neuromation.client import AbstractTreeProgress


class ImageProgress(AbstractTreeProgress):
    def message(self, message: str, branch: Optional["str"] = None) -> None:
        pass

    @classmethod
    def create(cls, tty: bool, quiet: bool) -> "ImageProgress":
        if quiet:
            return ImageProgress()
        elif tty:
            return DetailedImageProgress()
        return StreamImageProgress()


class DetailedImageProgress(ImageProgress):
    def __init__(self) -> None:
        self._mapping: Dict[str, int] = {}
        self._reporter = MultilineReporter()

    def message(self, message: str, branch: Optional[str] = None) -> None:
        if branch:
            if branch in self._mapping.keys():
                lineno = self._mapping[branch]
                self._reporter.report(message, lineno)
            else:
                self._reporter.report(message)
                self._mapping[branch] = self._reporter.total_lines
        else:
            self._reporter.report(message)

    def close(self) -> None:
        self._reporter.close()


class StreamImageProgress(ImageProgress):
    def __init__(self) -> None:
        self._reporter = StreamReporter()
        pass

    def message(self, message: str, branch: Optional["str"] = None) -> None:
        if branch:
            self._reporter.tick()
        else:
            self._reporter.report(message)

    def close(self) -> None:
        self._reporter.close()
