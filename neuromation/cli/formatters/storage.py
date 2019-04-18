import abc
import enum
import operator
import os
import time
from fnmatch import fnmatch
from math import ceil
from typing import Any, Dict, Iterator, List, Sequence

import humanize
from click import style, unstyle

from neuromation.api import Action, FileStatus, FileStatusType


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


class GnuIndicators(str, enum.Enum):
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
    PS_CARRET = enum.auto()


class BasePainter(abc.ABC):
    @abc.abstractmethod
    def paint(self, label: str, file: FileStatus) -> str:  # pragma: no cover
        pass


class NonePainter(BasePainter):
    def paint(self, label: str, file: FileStatus) -> str:
        return label


class GnuPainter(BasePainter):
    def __init__(self, ls_colors: str):
        self._defaults()
        self._parse_ls_colors(ls_colors)

    def _defaults(self) -> None:
        self.color_indicator: Dict[GnuIndicators, str] = {
            GnuIndicators.LEFT: "\033[",
            GnuIndicators.RIGHT: "m",
            GnuIndicators.END: "",
            GnuIndicators.RESET: "0",
            GnuIndicators.NORM: "",
            GnuIndicators.FILE: "",
            GnuIndicators.DIR: "01;34",
            GnuIndicators.LINK: "01;36",
            GnuIndicators.FIFO: "33",
            GnuIndicators.SOCKET: "01;35",
            GnuIndicators.BLK: "01;33",
            GnuIndicators.CHR: "01;33",
            GnuIndicators.MISSING: "",
            GnuIndicators.ORPHAN: "",
            GnuIndicators.EXEC: "01;32",
            GnuIndicators.DOOR: "01;35",
            GnuIndicators.SETUID: "37;41",
            GnuIndicators.SETGID: "30;43",
            GnuIndicators.STICKY: "37;44",
            GnuIndicators.OTHER_WRITABLE: "34;42",
            GnuIndicators.STICKY_OTHER_WRITABLE: "30;42",
            GnuIndicators.CAP: "30;41",
            GnuIndicators.MULTI_HARD_LINK: "",
            GnuIndicators.CLR_TO_EOL: "\033[K",
        }
        self.color_ext_type: Dict[str, str] = {}

    def _parse_ls_colors(self, ls_colors: str) -> None:
        def process(left: str, right: str) -> None:
            try:
                self.color_indicator[GnuIndicators(left)] = right
            except ValueError:
                self.color_ext_type[left] = right

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
                    if num > 7:
                        state = ParseState.PS_ESCAPED_END
                        escaped = chr(num)
                    pos += 1
                else:
                    state = ParseState.PS_ESCAPED_END
                    escaped = chr(num)
            elif state == ParseState.PS_HEX:
                if char in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                    num = num * 16 + ord(char) - ord("0")
                    if num > 15:
                        state = ParseState.PS_ESCAPED_END
                        escaped = chr(num)
                    pos += 1
                elif char.upper() in ["A", "B", "C", "D", "E", "F"]:
                    num = num * 16 + 10 + ord(char.upper()) - ord("A")
                    if num > 15:
                        state = ParseState.PS_ESCAPED_END
                        escaped = chr(num)
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
                    num = 0
                elif char.upper() == "X":
                    stack.append(state)
                    state = ParseState.PS_HEX
                    num = 0
                    pos += 1

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
            elif state == ParseState.PS_CARRET:
                if "@" <= char <= "~":
                    escaped = chr(ord(char) & 0o37)
                elif char == "?":
                    escaped = chr(127)
                else:
                    raise EnvironmentError("Cannot parse coloring scheme")
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
                elif char == "^":
                    stack.append(state)
                    state = ParseState.PS_CARRET
                    pos += 1
                    escaped = ""
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
                elif char == "^":
                    stack.append(state)
                    state = ParseState.PS_CARRET
                    pos += 1
                    escaped = ""
                else:
                    right += char
                    pos += 1

        if state == ParseState.PS_CARRET:
            raise EnvironmentError("Cannot parse coloring scheme")
        if state in [ParseState.PS_HEX, ParseState.PS_OCTAL]:
            escaped = chr(num)
            state = stack.pop()
        if state == ParseState.PS_ESCAPED:
            stack.append(ParseState.PS_ESCAPED)
            state = ParseState.PS_ESCAPED_END
        if state == ParseState.PS_ESCAPED_END:
            stack.pop()
            state = stack.pop()
            if state == ParseState.PS_RIGHT:  # pragma no branch
                right += escaped
        if state == ParseState.PS_RIGHT and len(right):
            process(left, right)

    def paint(self, label: str, file: FileStatus) -> str:
        mapping = {
            FileStatusType.FILE: self.color_indicator[GnuIndicators.FILE],
            FileStatusType.DIRECTORY: self.color_indicator[GnuIndicators.DIR],
        }
        color = mapping[file.type]
        if not color:
            color = self.color_indicator[GnuIndicators.NORM]
        if file.type == FileStatusType.FILE:
            for pattern, value in self.color_ext_type.items():
                if fnmatch(file.name, pattern):
                    color = value
                    break
        if color:
            return (
                self.color_indicator[GnuIndicators.LEFT]
                + color
                + self.color_indicator[GnuIndicators.RIGHT]
                + label
                + self.color_indicator[GnuIndicators.LEFT]
                + self.color_indicator[GnuIndicators.RESET]
                + self.color_indicator[GnuIndicators.RIGHT]
            )
        return label


class BSDAttributes(enum.Enum):
    DIRECTORY = 1
    LINK = 2
    SOCKET = 3
    PIPE = 4
    EXECUTABLE = 5
    BLOCK = 6
    CHARACTER = 7
    EXECUTABLE_SETUID = 8
    EXECUTABLE_SETGID = 9
    DIRECTORY_WRITABLE_OTHERS_WITH_STICKY = 10
    DIRECTORY_WRITABLE_OTHERS_WITHOUT_STICKY = 11


class BSDPainter(BasePainter):
    def __init__(self, lscolors: str):
        self._parse_lscolors(lscolors)

    def _parse_lscolors(self, lscolors: str) -> None:
        parts = chunks(lscolors, 2)
        self._colors: Dict[BSDAttributes, str] = {}
        num = 0
        for attr in BSDAttributes:
            self._colors[attr] = parts[num]
            num += 1

    def paint(self, label: str, file: FileStatus) -> str:
        color = ""
        if file.type == FileStatusType.DIRECTORY:
            color = self._colors[BSDAttributes.DIRECTORY]
        if color:
            char_to_color = {
                "a": "black",
                "b": "red",
                "c": "green",
                "d": "brown",
                "e": "blue",
                "f": "magenta",
                "g": "cyan",
                "h": "white",
            }
            bold = None
            fg = bg = None
            if color[0].lower() in char_to_color.keys():
                fg = char_to_color[color[0].lower()]
                if color[0].isupper():
                    bold = True
            if color[1] in char_to_color.keys():
                bg = char_to_color[color[1]]
            if fg or bg or bold:
                return style(label, fg=fg, bg=bg, bold=bold)
        return label


class PainterFactory:
    @classmethod
    def detect(cls, color: bool) -> BasePainter:
        if color:
            ls_colors = os.getenv("LS_COLORS")
            if ls_colors:
                return GnuPainter(ls_colors)
            lscolors = os.getenv("LSCOLORS")
            if lscolors:
                return BSDPainter(lscolors)

            pass
        return NonePainter()


class BaseFilesFormatter:
    @abc.abstractmethod
    def __call__(
        self, files: Sequence[FileStatus]
    ) -> Iterator[str]:  # pragma: no cover
        pass


class LongFilesFormatter(BaseFilesFormatter):
    permissions_mapping = {Action.MANAGE: "m", Action.WRITE: "w", Action.READ: "r"}

    file_types_mapping = {FileStatusType.FILE: "-", FileStatusType.DIRECTORY: "d"}

    def __init__(self, human_readable: bool, color: bool):
        self.human_readable = human_readable
        self.painter = PainterFactory.detect(color)

    def _columns_for_file(self, file: FileStatus) -> Sequence[str]:

        type = self.file_types_mapping[file.type]
        permission = self.permissions_mapping[Action(file.permission)]

        date = time.strftime(TIME_FORMAT, time.localtime(file.modification_time))

        size = file.size
        if self.human_readable:
            size = humanize.naturalsize(size, gnu=True).rstrip("B")

        name = self.painter.paint(file.name, file)

        return [f"{type}{permission}", f"{size}", f"{date}", f"{name}"]

    def __call__(self, files: Sequence[FileStatus]) -> Iterator[str]:
        if not files:
            return
        table = [self._columns_for_file(file) for file in files]
        widths = [0 for _ in table[0]]
        for row in table:
            for x in range(len(row)):
                cell_width = len(unstyle(row[x]))
                if widths[x] < cell_width:
                    widths[x] = cell_width
        for row in table:
            line = []
            for x in range(len(row)):
                if x == len(row) - 1:
                    line.append(row[x])
                else:
                    line.append(row[x].rjust(widths[x]))
            yield " ".join(line)


class SimpleFilesFormatter(BaseFilesFormatter):
    def __init__(self, color: bool):
        self.painter = PainterFactory.detect(color)

    def __call__(self, files: Sequence[FileStatus]) -> Iterator[str]:
        for file in files:
            yield self.painter.paint(file.name, file)


class VerticalColumnsFilesFormatter(BaseFilesFormatter):
    def __init__(self, width: int, color: bool):
        self.width = width
        self.painter = PainterFactory.detect(color)

    def __call__(self, files: Sequence[FileStatus]) -> Iterator[str]:
        if not files:
            return
        items = [self.painter.paint(file.name, file) for file in files]
        widths = [len(unstyle(item)) for item in items]
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
        field = None
        if self == self.NAME:
            field = "name"
        elif self == self.SIZE:
            field = "size"
        elif self == self.TIME:
            field = "modification_time"
        assert field
        return operator.attrgetter(field)
