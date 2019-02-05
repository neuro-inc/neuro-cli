import abc
import datetime
import enum
import time
from math import ceil
from typing import Any, Iterator, List, Sequence

import humanize

from neuromation.cli.formatter import BaseFormatter
from neuromation.client.storage import FileStatus, FileStatusType


RECENT_TIME_DELTA = 365 * 24 * 60 * 60 / 2


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


class BaseFileFormatter(BaseFormatter, abc.ABC):
    @abc.abstractmethod
    def min_width(self, file: FileStatus) -> int:  # pragma: no cover
        pass

    def min_width_list(self, files: Sequence[FileStatus]) -> Sequence[int]:
        return [self.min_width(file) for file in files]

    @abc.abstractmethod
    def format(self, file: FileStatus, width: int) -> str:  # pragma: no cover
        pass

    def format_list(self, files: Sequence[FileStatus], width: int) -> Sequence[str]:
        return [self.format(file, width) for file in files]


class ShortFileFormatter(BaseFileFormatter):
    def __init__(self, quoted: bool = False):
        self.quoted = quoted

    def min_width(self, file: FileStatus) -> int:
        if self.quoted:
            return 2 + len(file.name)
        return len(file.name)

    def format(self, file: FileStatus, width: int) -> str:
        result = file.name
        if self.quoted:
            result = f'"{result}"'
        return result


class LongFileFormatter(BaseFileFormatter):
    def __init__(
        self,
        separator: str = " ",
        time_format: str = "%c",
        recent_time_format: str = "",
        human_readable: bool = False,
        quoted: bool = False,
    ):
        self.separator = separator
        self.time_format = time_format
        if recent_time_format:
            self.recent_time_format = recent_time_format
        else:
            self.recent_time_format = self.time_format
        self.human_readable = human_readable
        self.quoted = quoted

    def min_width(self, file: FileStatus) -> int:
        raise NotImplementedError()

    def format(self, file: FileStatus, width: int) -> str:
        raise NotImplementedError()

    def parts(self, file: FileStatus) -> Sequence[str]:
        type = "-"
        if file.type == FileStatusType.DIRECTORY:
            type = "d"

        permission = file.permission[0]

        time_format = self.time_format
        if abs(file.modification_time - time.time()) < RECENT_TIME_DELTA:
            time_format = self.recent_time_format
        date = datetime.datetime.fromtimestamp(file.modification_time).strftime(
            time_format
        )

        size = file.size
        if self.human_readable:
            size = humanize.naturalsize(size, gnu=True).rstrip("B")

        name = file.name
        if self.quoted:
            name = f'"{name}"'

        return [f"{type}{permission}", f"{size}", f"{date}", f"{name}"]

    def parts_list(self, files: Sequence[FileStatus]) -> Sequence[Sequence[str]]:
        return [self.parts(file) for file in files]

    def format_list(self, files: Sequence[FileStatus], width: int) -> Sequence[str]:
        table = self.parts_list(files)
        widths = [0 for _ in table[0]]
        for row in table:
            for x in range(len(row)):
                if widths[x] < len(row[x]):
                    widths[x] = len(row[x])
        result: List[str] = []
        for row in table:
            line = []
            for x in range(len(row)):
                if x == len(row) - 1:
                    line.append(row[x])
                else:
                    line.append(row[x].rjust(widths[x]))
            result.append(self.separator.join(line))
        return result


class BaseLayout(BaseFormatter, abc.ABC):
    @abc.abstractmethod
    def format(
        self, file_formatter: BaseFileFormatter, files: Sequence[FileStatus]
    ) -> Iterator[str]:  # pragma: no cover
        pass


class SingleColumnLayout(BaseLayout):
    def format(
        self, file_formatter: BaseFileFormatter, files: Sequence[FileStatus]
    ) -> Iterator[str]:
        formatted = file_formatter.format_list(files, 0)
        for line in formatted:
            yield line


class AcrossLayout(BaseLayout):
    def __init__(self, max_width: int = None, separator: str = "  "):
        self.max_width = max_width
        self.separator = separator

    def format(
        self, file_formatter: BaseFileFormatter, files: Sequence[FileStatus]
    ) -> Iterator[str]:
        # simple case, no width limits
        if not self.max_width:
            yield self.separator.join(file_formatter.format_list(files, 0))
            return

        widths = file_formatter.min_width_list(files)

        # let`s check how many columns we can use
        test_count = 1
        while True:
            test_rows = chunks(widths, test_count)
            test_columns = transpose(test_rows)
            test_columns_width = [max(column) for column in test_columns]
            test_total_width = sum(test_columns_width) + (len(test_columns) - 1) * len(
                self.separator
            )
            if test_count == 1 or test_total_width <= self.max_width:
                count = test_count
                columns_width = test_columns_width
                if test_total_width == self.max_width:
                    break

            if test_total_width >= self.max_width or len(test_columns) == len(files):
                break
            test_count = test_count + 1

        rows = chunks(files, count)
        for row in rows:
            formatted_row = []
            for i in range(len(row)):
                formatted = file_formatter.format(row[i], columns_width[i])
                if i < len(row) - 1:
                    formatted = formatted.ljust(columns_width[i])
                formatted_row.append(formatted)
            yield self.separator.join(formatted_row)


class VerticalLayout(BaseLayout):
    def __init__(self, max_width: int = None, separator: str = "  "):
        self.max_width = max_width
        self.separator = separator

    def format(
        self, file_formatter: BaseFileFormatter, files: Sequence[FileStatus]
    ) -> Iterator[str]:
        # simple case, no width limits
        if not self.max_width:
            yield self.separator.join(file_formatter.format_list(files, 0))
            return

        widths = file_formatter.min_width_list(files)

        # let`s check how many columns we can use
        test_count = 1
        while True:
            test_columns = chunks(widths, ceil(len(files) / test_count))
            test_columns_width = [max(column) for column in test_columns]
            test_total_width = sum(test_columns_width) + (len(test_columns) - 1) * len(
                self.separator
            )
            if test_count == 1 or test_total_width <= self.max_width:
                count = test_count
                columns_width = test_columns_width
                if test_total_width == self.max_width:
                    break

            if test_total_width >= self.max_width or len(test_columns) == len(files):
                break
            test_count = test_count + 1

        rows = transpose(chunks(files, ceil(len(files) / count)))
        for row in rows:
            formatted_row = []
            for i in range(len(row)):
                formatted = file_formatter.format(row[i], columns_width[i])
                if i < len(row) - 1:
                    formatted = formatted.ljust(columns_width[i])
                formatted_row.append(formatted)
            yield self.separator.join(formatted_row)


class CommasLayout(BaseLayout):
    def __init__(self, max_width: int = 0, separator: str = ", "):
        self.max_width = max_width
        self.separator = separator

    def format(
        self, file_formatter: BaseFileFormatter, files: Sequence[FileStatus]
    ) -> Iterator[str]:
        formatted_files = file_formatter.format_list(files, 0)
        if not self.max_width:
            yield self.separator.join(formatted_files)
            return
        row = ""
        for i in range(len(formatted_files)):
            if i == len(formatted_files) - 1:
                separator = ""
            else:
                separator = self.separator
            formatted = formatted_files[i]
            test = row + formatted + separator
            if len(test) >= self.max_width:
                if row:
                    yield row
                    row = formatted + separator
                else:
                    yield test
                    row = ""
            else:
                row = test
        if row:
            yield row


class Sorter(str, enum.Enum):
    NAME = "name"
    NONE = "none"
    SIZE = "size"
    TIME = "time"

    def sort(
        self,
        files: List[FileStatus],
        reverse: bool = False,
        group_directories_first: bool = False,
    ) -> None:
        if self == self.NONE:
            return
        if self == self.NAME:
            files.sort(
                key=lambda x: (
                    group_directories_first
                    and ((x.type == FileStatusType.FILE) ^ reverse),
                    x.name,
                ),
                reverse=reverse,
            )
        elif self == self.SIZE:
            files.sort(
                key=lambda x: (
                    group_directories_first
                    and ((x.type == FileStatusType.FILE) ^ reverse),
                    x.size,
                ),
                reverse=reverse,
            )
        elif self == self.TIME:
            files.sort(
                key=lambda x: (
                    group_directories_first
                    and ((x.type == FileStatusType.FILE) ^ reverse),
                    x.modification_time,
                ),
                reverse=reverse,
            )
