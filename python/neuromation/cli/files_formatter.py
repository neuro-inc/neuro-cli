import abc
import enum
import operator
import time
from math import ceil
from typing import Any, Iterator, List, Sequence

import humanize

from neuromation.cli.formatter import BaseFormatter
from neuromation.client import Action, FileStatus, FileStatusType


RECENT_TIME_DELTA = 365 * 24 * 60 * 60 / 2
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def chunks(list: Sequence[Any], size: int) -> Sequence[Any]:
    result = []
    for i in range(0, len(list), size):
        result.append(list[i : i + size])
    return result


def transpose(columns: Sequence[Sequence[Any]]) -> Sequence[Sequence[Any]]:
    height = len(columns)
    width = len(columns[0])
    result: Sequence[List[Any]] = [[] for _ in range(width)]
    for i in range(width):
        for j in range(height):
            if i < len(columns[j]):
                result[i].append(columns[j][i])
    return result


class BaseFilesFormatter(BaseFormatter, abc.ABC):
    def __call__(
        self, files: Sequence[FileStatus]
    ) -> Iterator[str]:  # pragma: no cover
        pass


class LongFilesFormatter(BaseFilesFormatter):
    permissions_mapping = {Action.MANAGE: "m", Action.WRITE: "w", Action.READ: "r"}

    file_types_mapping = {FileStatusType.FILE: "-", FileStatusType.DIRECTORY: "d"}

    def __init__(self, human_readable: bool = False):
        self.human_readable = human_readable

    def _columns_for_file(self, file: FileStatus) -> Sequence[str]:

        type = self.file_types_mapping[file.type]
        permission = self.permissions_mapping[Action(file.permission)]

        date = time.strftime(TIME_FORMAT, time.localtime(file.modification_time))

        size = file.size
        if self.human_readable:
            size = humanize.naturalsize(size, gnu=True).rstrip("B")

        name = file.name

        return [f"{type}{permission}", f"{size}", f"{date}", f"{name}"]

    def __call__(self, files: Sequence[FileStatus]) -> Iterator[str]:
        if not files:
            return
        table = [self._columns_for_file(file) for file in files]
        widths = [0 for _ in table[0]]
        for row in table:
            for x in range(len(row)):
                if widths[x] < len(row[x]):
                    widths[x] = len(row[x])
        for row in table:
            line = []
            for x in range(len(row)):
                if x == len(row) - 1:
                    line.append(row[x])
                else:
                    line.append(row[x].rjust(widths[x]))
            yield " ".join(line)


class SimpleFilesFormatter(BaseFilesFormatter):
    def __call__(self, files: Sequence[FileStatus]) -> Iterator[str]:
        for file in files:
            yield file.name


class VerticalColumnsFilesFormatter(BaseFilesFormatter):
    def __init__(self, width: int):
        self.width = width

    def __call__(self, files: Sequence[FileStatus]) -> Iterator[str]:
        if not files:
            return
        items = [file.name for file in files]
        widths = [len(item) for item in items]
        # let`s check how many columns we can use
        test_count = 1
        while True:
            test_columns = chunks(widths, ceil(len(items) / test_count))
            test_columns_widths = [max(column) for column in test_columns]
            test_total_width = sum(test_columns_widths) + 2 * (len(test_columns) - 1)
            if test_count == 1 or test_total_width <= self.width:
                count = test_count
                columns_widths = test_columns_widths
                if test_total_width == self.width:
                    break

            if test_total_width >= self.width or len(test_columns) == len(items):
                break
            test_count = test_count + 1

        rows = transpose(chunks(items, ceil(len(items) / count)))
        for row in rows:
            formatted_row = []
            for i in range(len(row)):
                formatted = row[i]
                if i < len(row) - 1:
                    formatted = formatted.ljust(columns_widths[i])
                formatted_row.append(formatted)
            yield "  ".join(formatted_row)


class FilesSorter(str, enum.Enum):
    NAME = "name"
    SIZE = "size"
    TIME = "time"

    def key(self) -> Any:
        if self == self.NAME:
            field = "name"
        elif self == self.SIZE:
            field = "size"
        elif self == self.TIME:
            field = "modification_time"
        return operator.attrgetter(field)
