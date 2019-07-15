from typing import Optional

import click
from yarl import URL

from neuromation.api import AbstractStorageProgress


class ProgressBase(AbstractStorageProgress):
    def start(self, src: URL, dst: URL, size: int) -> None:
        pass

    def complete(self, src: URL, dst: URL) -> None:
        click.echo(f"{src!r} -> {dst!r}")

    def progress(self, src: URL, dst: URL, current: int) -> None:
        pass

    def mkdir(self, src: URL, dst: URL) -> None:
        click.echo(f"{src!r} -> {dst!r}")

    def fail(self, src: URL, dst: URL, message: str) -> None:  # pragma: no cover
        click.echo(f"Failure: {src:!} -> {dst!r} [{message}]", err=True)

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
        self._src: Optional[URL] = None
        self._dst: Optional[URL] = None
        self._file_size: Optional[int] = None

    def start(self, src: URL, dst: URL, size: int) -> None:
        self._src = src
        self._dst = dst
        self._file_size = size
        click.echo(f"Start copying {self._src!r} -> {self._dst!r}.")

    def complete(self, src: URL, dst: URL) -> None:
        self._src = src
        self._dst = dst
        click.echo(f"\rFile {self._src!r} -> {self._dst!r} copying completed.")

    def progress(self, src: URL, dst: URL, current: int) -> None:
        self._src = src
        self._dst = dst
        if self._file_size:
            progress = (100 * current) / self._file_size
        else:
            progress = 0
        click.echo(f"\r{self._src!r} -> {self._dst!r}: {progress:.2f}%.", nl=False)

    def mkdir(self, src: URL, dst: URL) -> None:
        click.echo(f"Copy directory {src!r} -> {dst!r}.")

    def fail(self, src: URL, dst: URL, message: str) -> None:  # pragma: no cover
        click.echo(f"Failure: {src:!} -> {dst!r} [{message}]", err=True)
