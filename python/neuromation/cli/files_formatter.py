import abc
import enum
from itertools import cycle
from math import ceil
from typing import Iterator, List, Type

from neuromation.cli.formatter import BaseFormatter
from neuromation.client.storage import FileStatus, FileStatusType


def chunks(list: List, size: int) -> List:
    result = []
    for i in range(0, len(list), size):
        result.append(list[i : i + size])
    return result


def transpose(columns: List) -> List:
    height = len(columns)
    width = len(columns[0])
    result = [[] for _ in range(width)]
    for i in range(width):
        for j in range(height):
            if i < len(columns[j]):
                result[i].append(columns[j][i])
    return result


class BaseFileFormatter(BaseFormatter, abc.ABC):
    @abc.abstractmethod
    def min_width(self, file: FileStatus) -> int:
        pass

    def min_width_list(self, files: List[FileStatus]) -> List[int]:
        return [self.min_width(file) for file in files]

    @abc.abstractmethod
    def format(self, file: FileStatus, width: int) -> str:
        pass

    def format_list(self, files: List[FileStatus], width: int) -> List[str]:
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


class BaseLayout(BaseFormatter, abc.ABC):
    @abc.abstractmethod
    def format(
        self, file_formatter: BaseFileFormatter, files: List[FileStatus]
    ) -> Iterator[str]:
        pass


class SingleColumnLayout(BaseLayout):
    def format(
        self, file_formatter: BaseFileFormatter, files: List[FileStatus]
    ) -> Iterator[str]:
        for file in files:
            yield file_formatter.format(file, 0)


class AcrossLayout(BaseLayout):
    def __init__(self, max_width: int = None, separator: str = "  "):
        self.max_width = max_width
        self.separator = separator

    def format(
        self, file_formatter: BaseFileFormatter, files: List[FileStatus]
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
        self, file_formatter: BaseFileFormatter, files: List[FileStatus]
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
    def __init__(self, max_width: int = 0, separator=", "):
        self.max_width = max_width
        self.separator = separator

    def format(
        self, file_formatter: BaseFileFormatter, files: List[FileStatus]
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


class Order(str, enum.Enum):
    NAME = "name"
    NONE = "none"
    SIZE = "size"
