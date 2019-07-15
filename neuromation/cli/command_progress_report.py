from typing import Optional

import click
from yarl import URL

from neuromation.api import AbstractStorageProgress
from neuromation.api.url_utils import _extract_path


class ProgressBase(AbstractStorageProgress):
    def start(self, src: URL, dst: URL, size: int) -> None:
        pass

    def complete(self, src_url: URL, dst_url: URL) -> None:
        src = self.fmt_url(src_url)
        dst = self.fmt_url(dst_url)
        click.echo(f"{src!r} -> {dst!r}")

    def progress(self, src: URL, dst: URL, current: int) -> None:
        pass

    def mkdir(self, src_url: URL, dst_url: URL) -> None:
        src = self.fmt_url(src_url)
        dst = self.fmt_url(dst_url)
        click.echo(f"{src!r} -> {dst!r}")

    def fail(self, src_url: URL, dst_url: URL, message: str) -> None:
        src = self.fmt_url(src_url)
        dst = self.fmt_url(dst_url)
        click.echo(f"Failure: {src:!} -> {dst!r} [{message}]", err=True)

    def fmt_url(self, url: URL) -> str:
        if url.scheme == "file":
            path = _extract_path(url)
            return str(path)
        else:
            return str(url)

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

    def start(self, src: URL, dst: URL, size: int) -> None:
        self._src = self.fmt_url(src)
        self._dst = self.fmt_url(dst)
        self._file_size = size
        click.echo(f"Start copying {self._src!r} -> {self._dst!r}.")

    def complete(self, src: URL, dst: URL) -> None:
        self._src = self.fmt_url(src)
        self._dst = self.fmt_url(dst)
        click.echo(f"\rFile {self._src!r} -> {self._dst!r} copying completed.")

    def progress(self, src: URL, dst: URL, current: int) -> None:
        self._src = self.fmt_url(src)
        self._dst = self.fmt_url(dst)
        if self._file_size:
            progress = (100 * current) / self._file_size
        else:
            progress = 0
        click.echo(f"\r{self._src!r} -> {self._dst!r}: {progress:.2f}%.", nl=False)

    def mkdir(self, src_url: URL, dst_url: URL) -> None:
        src = self.fmt_url(src_url)
        dst = self.fmt_url(dst_url)
        click.echo(f"Copy directory {src!r} -> {dst!r}.")

    def fail(self, src_url: URL, dst_url: URL, message: str) -> None:
        src = self.fmt_url(src_url)
        dst = self.fmt_url(dst_url)
        click.echo(f"Failure: {src:!} -> {dst!r} [{message}]", err=True)
