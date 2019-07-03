from typing import Optional

from neuromation.api import AbstractProgress


class ProgressBase(AbstractProgress):
    def start(self, src: str, dst: str, size: int) -> None:
        pass

    def complete(self, src: str, dst: str) -> None:
        print(f"{src!r} -> {dst!r}")

    def progress(self, src: str, dst: str, current: int) -> None:
        pass

    def mkdir(self, src: str, dst: str) -> None:
        print(f"{src!r} -> {dst!r}")

    @classmethod
    def create_progress(
        cls, show_progress: bool, verbose: bool
    ) -> "Optional[ProgressBase]":
        if show_progress:
            return StandardPrintPercentOnly()
        if verbose:
            return ProgressBase()
        return None


class StandardPrintPercentOnly(ProgressBase):
    def __init__(self) -> None:
        self._src: Optional[str] = None
        self._dst: Optional[str] = None
        self._file_size: Optional[int] = None

    def start(self, src: str, dst: str, size: int) -> None:
        self._src = src
        self._dst = dst
        self._file_size = size
        print(f"Start copying {self._src!r} -> {self._dst!r}.")

    def complete(self, src: str, dst: str) -> None:
        self._src = src
        self._dst = dst
        print(f"\rFile {self._src!r} -> {self._dst!r} copying completed.")

    def progress(self, src: str, dst: str, current: int) -> None:
        self._src = src
        self._dst = dst
        if self._file_size:
            progress = (100 * current) / self._file_size
        else:
            progress = 0
        print(f"\r{self._src!r} -> {self._dst!r}: {progress:.2f}%.", end="")

    def mkdir(self, src: str, dst: str) -> None:
        print(f"Copy directory {src!r} -> {dst!r}.")
