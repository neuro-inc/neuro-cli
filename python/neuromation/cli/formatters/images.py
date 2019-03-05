from typing import Mapping, Optional

from neuromation.cli.command_reporter import MultilineReporter, StreamReporter
from neuromation.client import AbstractTreeProgress


class ImageProgress(AbstractTreeProgress):
    @classmethod
    def create(cls, tty: bool, quiet: bool) -> "ImageProgress":
        if quiet:
            return QuietImageProgress()
        elif tty:
            return DetailedImageProgress()
        return StreamImageProgress()


class DetailedImageProgress(ImageProgress):
    def __init__(self):
        self._mapping: Mapping[str, int] = {}
        self._reporter = MultilineReporter()

    def message(self, message: str, branch: Optional["str"] = None):
        if branch:
            if branch in self._mapping.keys():
                lineno = self._mapping[branch]
                self._reporter.report(message, lineno)
            else:
                self._mapping[branch] = self._reporter.report(message)
        else:
            self._reporter.report(message)

    def close(self):
        self._reporter.close()


class StreamImageProgress(ImageProgress):
    def __init__(self):
        self._reporter = StreamReporter()
        pass

    def message(self, message: str, branch: Optional["str"] = None):
        if branch:
            self._reporter.tick()
        else:
            self._reporter.report(message)

    def close(self):
        self._reporter.close()


class QuietImageProgress(ImageProgress):
    def message(self, message: str, branch: Optional["str"] = None):
        pass
