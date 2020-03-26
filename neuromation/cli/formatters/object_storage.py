import abc
import time
from functools import singledispatch
from typing import Iterator, Sequence, Union

from neuromation.api import (
    Action,
    BucketListing,
    FileStatusType,
    ObjectListing,
    PrefixListing,
)
from neuromation.cli.utils import format_size

from ..text_helper import StyledTextHelper
from .storage import TIME_FORMAT, get_painter


ObjectListings = Union[BucketListing, ObjectListing, PrefixListing]


def get_file_type(file: ObjectListings) -> FileStatusType:
    if file.is_dir():
        return FileStatusType.DIRECTORY
    else:
        return FileStatusType.FILE


class BaseObjectFormatter:
    @abc.abstractmethod
    def __call__(
        self, files: Sequence[ObjectListings]
    ) -> Iterator[str]:  # pragma: no cover
        pass


class LongObjectFormatter(BaseObjectFormatter):
    permissions_mapping = {Action.MANAGE: "m", Action.WRITE: "w", Action.READ: "r"}

    def __init__(self, human_readable: bool, color: bool):
        self.human_readable = human_readable
        self.painter = get_painter(color)

    @singledispatch
    def to_columns(self, file: ObjectListings) -> Sequence[str]:
        # Permission Size Date Name
        return ["", "", "", file.name]

    @to_columns.register
    def to_columns_bucket(self, file: BucketListing) -> Sequence[str]:
        permission = self.permissions_mapping[file.permission]
        date = time.strftime(TIME_FORMAT, time.localtime(file.creation_time))
        name = self.painter.paint(str(file.uri), get_file_type(file))
        return [f"b{permission}", f"", f"{date}", f"{name}"]

    @to_columns.register
    def to_columns_object(self, file: ObjectListing) -> Sequence[str]:
        date = time.strftime(TIME_FORMAT, time.localtime(file.modification_time))
        if self.human_readable:
            size = format_size(file.size).rstrip("B")
        else:
            size = str(file.size)
        name = self.painter.paint(str(file.uri), get_file_type(file))
        return ["o", f"{size}", f"{date}", f"{name}"]

    @to_columns.register
    def to_columns_prefix(self, file: PrefixListing) -> Sequence[str]:
        name = self.painter.paint(str(file.uri), get_file_type(file))
        return ["p", "", "", f"{name}"]

    def __call__(self, files: Sequence[ObjectListings]) -> Iterator[str]:
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


class SimpleObjectFormatter(BaseObjectFormatter):
    def __init__(self, color: bool):
        self.painter = get_painter(color)

    def __call__(self, files: Sequence[ObjectListings]) -> Iterator[str]:
        for file in files:
            yield self.painter.paint(str(file.uri), get_file_type(file))
