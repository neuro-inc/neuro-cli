from typing import Optional

import click
from yarl import URL

from neuromation.api import (
    AbstractStorageProgress,
    StorageProgressComplete,
    StorageProgressFail,
    StorageProgressMkdir,
    StorageProgressStart,
    StorageProgressStep,
)
from neuromation.api.url_utils import _extract_path


class ProgressBase(AbstractStorageProgress):
    def start(self, data: StorageProgressStart) -> None:
        pass

    def complete(self, data: StorageProgressComplete) -> None:
        src = self.fmt_url(data.src)
        dst = self.fmt_url(data.dst)
        click.echo(f"{src!r} -> {dst!r}")

    def step(self, data: StorageProgressStep) -> None:
        pass

    def mkdir(self, data: StorageProgressMkdir) -> None:
        src = self.fmt_url(data.src)
        dst = self.fmt_url(data.dst)
        click.echo(f"{src!r} -> {dst!r}")

    def fail(self, data: StorageProgressFail) -> None:
        src = self.fmt_url(data.src)
        dst = self.fmt_url(data.dst)
        click.echo(f"Failure: {src!r} -> {dst!r} [{data.message}]", err=True)

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
    def start(self, data: StorageProgressStart) -> None:
        src = self.fmt_url(data.src)
        dst = self.fmt_url(data.dst)
        click.echo(f"Start copying {src!r} -> {dst!r}.")

    def complete(self, data: StorageProgressComplete) -> None:
        src = self.fmt_url(data.src)
        dst = self.fmt_url(data.dst)
        click.echo(f"\rFile {src!r} -> {dst!r} copying completed.")

    def step(self, data: StorageProgressStep) -> None:
        src = self.fmt_url(data.src)
        dst = self.fmt_url(data.dst)
        progress = (100 * data.current) / data.size
        click.echo(f"\r{src!r} -> {dst!r}: {progress:.2f}%.", nl=False)

    def mkdir(self, data: StorageProgressMkdir) -> None:
        src = self.fmt_url(data.src)
        dst = self.fmt_url(data.dst)
        click.echo(f"Copy directory {src!r} -> {dst!r}.")

    def fail(self, data: StorageProgressFail) -> None:
        src = self.fmt_url(data.src)
        dst = self.fmt_url(data.dst)
        click.echo(f"Failure: {src!r} -> {dst!r} [{data.message}]", err=True)
