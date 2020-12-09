import abc
import time
from typing import Sequence, Union

from rich.console import RenderableType
from rich.table import Table
from rich.text import Text

from neuro_sdk import Action, BlobListing, BucketListing, FileStatusType, PrefixListing

from neuro_cli.utils import format_size

from .storage import TIME_FORMAT, get_painter

BlobListings = Union[BucketListing, BlobListing, PrefixListing]


def get_file_type(file: BlobListings) -> FileStatusType:
    if file.is_dir():
        return FileStatusType.DIRECTORY
    else:
        return FileStatusType.FILE


class BaseBlobFormatter:
    @abc.abstractmethod
    def __call__(
        self, files: Sequence[BlobListings]
    ) -> RenderableType:  # pragma: no cover
        pass


class LongBlobFormatter(BaseBlobFormatter):
    permissions_mapping = {Action.MANAGE: "m", Action.WRITE: "w", Action.READ: "r"}

    def __init__(self, human_readable: bool, color: bool):
        self.human_readable = human_readable
        self.painter = get_painter(color)

    def to_row(self, file: BlobListings) -> Sequence[RenderableType]:
        if isinstance(file, BucketListing):
            return self.to_row_bucket(file)
        elif isinstance(file, BlobListing):
            return self.to_row_blob(file)
        else:
            return self.to_row_prefix(file)

    def to_row_bucket(self, file: BucketListing) -> Sequence[RenderableType]:
        permission = self.permissions_mapping[file.permission]
        date = time.strftime(TIME_FORMAT, time.localtime(file.creation_time))
        name = self.painter.paint(str(file.uri), get_file_type(file))
        return [f"{permission}", f"", f"{date}", name]

    def to_row_blob(self, file: BlobListing) -> Sequence[RenderableType]:
        date = time.strftime(TIME_FORMAT, time.localtime(file.modification_time))
        if self.human_readable:
            size = format_size(file.size).rstrip("B")
        else:
            size = str(file.size)
        name = self.painter.paint(str(file.uri), get_file_type(file))
        return ["", f"{size}", f"{date}", name]

    def to_row_prefix(self, file: PrefixListing) -> Sequence[RenderableType]:
        name = self.painter.paint(str(file.uri), get_file_type(file))
        return ["", "", "", name]

    def __call__(self, files: Sequence[BlobListings]) -> RenderableType:
        table = Table.grid(padding=(0, 2))
        table.add_column()  # Type/Permissions
        table.add_column(justify="right")  # Size
        table.add_column()  # Date
        table.add_column()  # Filename
        for file in files:
            table.add_row(*self.to_row(file))
        return table


class SimpleBlobFormatter(BaseBlobFormatter):
    def __init__(self, color: bool):
        self.painter = get_painter(color)

    def __call__(self, files: Sequence[BlobListings]) -> RenderableType:
        return Text("\n").join(
            self.painter.paint(str(file.uri), get_file_type(file)) for file in files
        )
