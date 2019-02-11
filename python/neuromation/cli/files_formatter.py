import abc
import enum
import operator
import os
import time
from math import ceil
from typing import Any, Dict, Iterator, List, Sequence

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


class Indicators(str, enum.Enum):
    LEFT = "lc"
    RIGHT = "rc"
    END = "ec"
    RESET = "rs"
    NORM = "no"
    FILE = "fi"
    DIR = "di"
    LINK = "ln"
    FIFO = "pi"
    SOCKET = "so"
    BLK = "bd"
    CHR = "cd"
    MISSING = "mi"
    ORPHAN = "or"
    EXEC = "ex"
    DOOR = "do"
    SETUID = "su"
    SETGID = "sg"
    STICKY = "st"
    OTHER_WRITABLE = "ow"
    STICKY_OTHER_WRITABLE = "tw"
    CAP = "ca"
    MULTI_HARD_LINK = "mh"
    CLR_TO_EOL = "cl"


class ParseState(enum.Enum):
    PS_START = enum.auto()
    PS_LEFT = enum.auto()
    PS_ESCAPED = enum.auto()
    PS_ESCAPED_END = enum.auto()
    PS_RIGHT = enum.auto()
    PS_OCTAL = enum.auto()
    PS_HEX = enum.auto()


class Painter:
    def __init__(self, color: bool):
        self._color = color
        if self._color:
            self._defaults()
            self._parse_env()

    def _defaults(self) -> None:
        self.color_indicator: Dict[Indicators, str] = {
            Indicators.LEFT: "\033[",
            Indicators.RIGHT: "m",
            Indicators.END: "",
            Indicators.RESET: "0",
            Indicators.NORM: "",
            Indicators.FILE: "",
            Indicators.DIR: "01;34",
            Indicators.LINK: "01;36",
            Indicators.FIFO: "33",
            Indicators.SOCKET: "01;35",
            Indicators.BLK: "01;33",
            Indicators.CHR: "01;33",
            Indicators.MISSING: "",
            Indicators.ORPHAN: "",
            Indicators.EXEC: "01;32",
            Indicators.DOOR: "01;35",
            Indicators.SETUID: "37;41",
            Indicators.SETGID: "30;43",
            Indicators.STICKY: "37;44",
            Indicators.OTHER_WRITABLE: "34;42",
            Indicators.STICKY_OTHER_WRITABLE: "30;42",
            Indicators.CAP: "30;41",
            Indicators.MULTI_HARD_LINK: "",
            Indicators.CLR_TO_EOL: "\033[K",
        }
        self.color_ext_type: Dict[str, str] = {}

    def _parse_env(self) -> None:
        def process(left: str, right: str) -> None:
            try:
                self.color_indicator[Indicators(left)] = right
            except ValueError:
                self.color_ext_type[left] = right

        ls_colors = os.getenv("LS_COLORS")
        if not ls_colors:
            self._color = False
            return

        pos = 0
        left = right = escaped = ""
        num = 0
        state = ParseState.PS_START
        stack: List[ParseState] = []
        while pos < len(ls_colors):
            char = ls_colors[pos]
            if state == ParseState.PS_START:
                if char == ":":  # ignore colon
                    pos += 1
                else:
                    left = ""
                    state = ParseState.PS_LEFT
            elif state == ParseState.PS_OCTAL:
                if char in ["0", "1", "2", "3", "4", "5", "6", "7"]:
                    num = num * 8 + ord(char) - ord("0")
                    pos += 1
                else:
                    state = ParseState.PS_ESCAPED_END
                    escaped = chr(num)
            elif state == ParseState.PS_HEX:
                if char in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                    num = num * 16 + ord(char) - ord("0")
                    pos += 1
                elif char.upper() in ["A", "B", "C", "D", "E", "F"]:
                    num = num * 16 + 10 + ord(char.upper()) - ord("A")
                    pos += 1
                else:
                    state = ParseState.PS_ESCAPED_END
                    escaped = chr(num)
            elif state == ParseState.PS_ESCAPED_END:
                stack.pop()
                state = stack.pop()
                if state == ParseState.PS_LEFT:
                    left += escaped
                else:
                    right += escaped
                escaped = ""
            elif state == ParseState.PS_ESCAPED:
                if char in ["0", "1", "2", "3", "4", "5", "6", "7"]:
                    stack.append(state)
                    state = ParseState.PS_OCTAL
                elif char.upper() == "X":
                    stack.append(state)
                    state = ParseState.PS_HEX
                elif char == "a":
                    escaped = "\a"
                    stack.append(state)
                    state = ParseState.PS_ESCAPED_END
                    pos += 1
                elif char == "b":
                    escaped = "\b"
                    stack.append(state)
                    state = ParseState.PS_ESCAPED_END
                    pos += 1
                elif char == "e":
                    escaped = chr(27)
                    stack.append(state)
                    state = ParseState.PS_ESCAPED_END
                    pos += 1
                elif char == "f":
                    escaped = "\f"
                    stack.append(state)
                    state = ParseState.PS_ESCAPED_END
                    pos += 1
                elif char == "n":
                    escaped = "\n"
                    stack.append(state)
                    state = ParseState.PS_ESCAPED_END
                    pos += 1
                elif char == "r":
                    escaped = "\r"
                    stack.append(state)
                    state = ParseState.PS_ESCAPED_END
                    pos += 1
                elif char == "t":
                    escaped = "\t"
                    stack.append(state)
                    state = ParseState.PS_ESCAPED_END
                    pos += 1
                elif char == "v":
                    escaped = "\v"
                    stack.append(state)
                    state = ParseState.PS_ESCAPED_END
                    pos += 1
                elif char == "?":
                    escaped = chr(127)
                    stack.append(state)
                    state = ParseState.PS_ESCAPED_END
                    pos += 1
                elif char == "_":
                    escaped = " "
                    stack.append(state)
                    state = ParseState.PS_ESCAPED_END
                    pos += 1
                elif char == chr(0):  # pragma: no cover
                    raise EnvironmentError("Cannot parse coloring scheme")
                else:
                    escaped = char
                    stack.append(state)
                    state = ParseState.PS_ESCAPED_END
                    pos += 1
            elif state == ParseState.PS_LEFT:
                if char == "\\":
                    stack.append(state)
                    state = ParseState.PS_ESCAPED
                    pos += 1
                    escaped = ""
                elif char == "=":
                    right = ""
                    state = ParseState.PS_RIGHT
                    pos += 1
                else:
                    left += char
                    pos = pos + 1
            elif state == ParseState.PS_RIGHT:
                if char == "\\":
                    stack.append(state)
                    state = ParseState.PS_ESCAPED
                    pos += 1
                    escaped = ""
                elif char == ":":
                    if right:
                        process(left, right)
                    state = ParseState.PS_START
                    pos += 1
                else:
                    right += char
                    pos += 1

        if state in [ParseState.PS_HEX, ParseState.PS_OCTAL]:
            escaped = chr(num)
            state = stack.pop()
        if state == ParseState.PS_ESCAPED:
            stack.append(ParseState.PS_ESCAPED)
            state = ParseState.PS_ESCAPED_END
        if state == ParseState.PS_ESCAPED_END:
            stack.pop()
            state = stack.pop()
            if state == ParseState.PS_LEFT:
                left += escaped
            else:
                right += escaped
        if state == ParseState.PS_RIGHT and len(right):
            process(left, right)


class BaseFilesFormatter(BaseFormatter, abc.ABC):
    def __call__(
        self, files: Sequence[FileStatus]
    ) -> Iterator[str]:  # pragma: no cover
        pass


class LongFilesFormatter(BaseFilesFormatter):
    permissions_mapping = {Action.MANAGE: "m", Action.WRITE: "w", Action.READ: "r"}

    file_types_mapping = {FileStatusType.FILE: "-", FileStatusType.DIRECTORY: "d"}

    def __init__(self, human_readable: bool, color: bool):
        self.human_readable = human_readable
        self.color = color

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
    def __init__(self, width: int, color: bool):
        self.width = width
        self.color = color

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
