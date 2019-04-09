from typing import Optional

from neuromation.api import AbstractProgress


class ProgressBase(AbstractProgress):
    def start(self, file: str, size: int) -> None:
        pass

    def complete(self, file: str) -> None:
        pass

    def progress(self, file: str, current: int) -> None:
        pass

    @classmethod
    def create_progress(cls, show_progress: bool) -> "ProgressBase":
        if show_progress:
            return StandardPrintPercentOnly()
        return ProgressBase()


class StandardPrintPercentOnly(ProgressBase):
    def __init__(self) -> None:
        self._file: Optional[str] = None
        self._file_size: Optional[int] = None

    def start(self, file: str, size: int) -> None:
        self._file = file
        self._file_size = size
        print(f"Starting file {file}.")

    def complete(self, file: str) -> None:
        self._file = file
        print(f"\rFile {file} upload complete.")

    def progress(self, file: str, current: int) -> None:
        self._file = file
        if self._file_size:
            progress = (100 * current) / self._file_size
        else:
            progress = 0
        print(f"\r{self._file}: {progress:.2f}%.", end="")
