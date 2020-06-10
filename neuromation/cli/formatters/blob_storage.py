import abc
import time
from typing import Iterator, Sequence, Union

from neuromation.api import (
    Action,
    BlobListing,
    BucketListing,
    FileStatusType,
    PrefixListing,
)
from neuromation.cli.utils import format_size

from ..text_helper import StyledTextHelper
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
    ) -> Iterator[str]:  # pragma: no cover
        pass


class LongBlobFormatter(BaseBlobFormatter):
    permissions_mapping = {Action.MANAGE: "m", Action.WRITE: "w", Action.READ: "r"}

    def __init__(self, human_readable: bool, color: bool):
        self.human_readable = human_readable
        self.painter = get_painter(color)

    def to_columns(self, file: BlobListings) -> Sequence[str]:
        if isinstance(file, BucketListing):
            return self.to_columns_bucket(file)
        elif isinstance(file, BlobListing):
            return self.to_columns_blob(file)
        else:
            return self.to_columns_prefix(file)

    def to_columns_bucket(self, file: BucketListing) -> Sequence[str]:
        permission = self.permissions_mapping[file.permission]
        date = time.strftime(TIME_FORMAT, time.localtime(file.creation_time))
        name = self.painter.paint(str(file.uri), get_file_type(file))
        return [f"{permission}", f"", f"{date}", f"{name}"]

    def to_columns_blob(self, file: BlobListing) -> Sequence[str]:
        date = time.strftime(TIME_FORMAT, time.localtime(file.modification_time))
        if self.human_readable:
            size = format_size(file.size).rstrip("B")
        else:
            size = str(file.size)
        name = self.painter.paint(str(file.uri), get_file_type(file))
        return ["", f"{size}", f"{date}", f"{name}"]

    def to_columns_prefix(self, file: PrefixListing) -> Sequence[str]:
        name = self.painter.paint(str(file.uri), get_file_type(file))
        return ["", "", "", f"{name}"]

    def __call__(self, files: Sequence[BlobListings]) -> Iterator[str]:
        if not files:
            return
        table = [self.to_columns(file) for file in files]
        widths = [0 for _ in table[0]]
        for row in table:
            for x in range(len(row)):
                cell_width = StyledTextHelper.width(row[x])
                if widths[x] < cell_width:
                    widths[x] = cell_width
        for row in table:
            line = []
            for x in range(len(row)):
                if x == len(row) - 1:
                    line.append(row[x])
                else:
                    line.append(StyledTextHelper.rjust(row[x], widths[x]))
            yield " ".join(line)


class SimpleBlobFormatter(BaseBlobFormatter):
    def __init__(self, color: bool):
        self.painter = get_painter(color)

    def __call__(self, files: Sequence[BlobListings]) -> Iterator[str]:
        for file in files:
            yield self.painter.paint(str(file.uri), get_file_type(file))
