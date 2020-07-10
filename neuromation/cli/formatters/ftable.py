from dataclasses import dataclass
from enum import Enum
from itertools import zip_longest
from typing import Any, Iterator, List, Optional, Sequence

from ..text_helper import StyledTextHelper


__all__ = ["table"]
__version__ = "0.1"


@dataclass(frozen=True)
class ColumnWidth:
    min: Optional[int] = None
    max: Optional[int] = None
    width: Optional[int] = None

    def __post_init__(self) -> None:
        if self.width and self.width < 0:
            raise ValueError("Width must be positive integer")
        if self.min and self.min < 0:
            raise ValueError("Min must be positive integer")
        if self.max and self.max < 0:
            raise ValueError("Max must be positive integer")


class Align(str, Enum):
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"


_align_to_format = {
    Align.LEFT: StyledTextHelper.ljust,
    Align.RIGHT: StyledTextHelper.rjust,
    Align.CENTER: StyledTextHelper.center,
    None: StyledTextHelper.ljust,
}


def table(
    rows: Sequence[Sequence[str]],
    widths: Sequence[ColumnWidth] = (),
    aligns: Sequence[Align] = (),
    max_width: Optional[int] = None,
) -> Iterator[str]:
    if not rows:
        return

    # Columns widths calculation
    if len(widths) < len(rows[0]):
        widths = tuple(widths) + tuple([ColumnWidth()]) * (len(rows[0]) - len(widths))
    calc_widths: List[int] = []
    for i, width in enumerate(widths):
        max_cell_width: int = max(StyledTextHelper.width(row[i]) for row in rows)
        width_min = width.min or width.width
        width_max = width.max or width.width

        if (not width_min or width_min <= max_cell_width) and (
            not width_max or width_max >= max_cell_width
        ):
            calc_widths.append(max_cell_width)
        elif width_max:
            calc_widths.append(width_max)
        elif width_min:
            calc_widths.append(width_min)

    # How many empty columns can be displayed
    max_empty_columns = len(rows[0])
    if max_width:
        sum_width = 0
        for i, column_width in enumerate(calc_widths):
            sum_width += column_width
            if sum_width > max_width:
                max_empty_columns = i
                break
            sum_width += 2

    for row in rows:
        for line in _row(row, calc_widths, aligns, max_width, max_empty_columns):
            yield line


def _row(
    fields: Sequence[str],
    widths: Sequence[int],
    aligns: Sequence[Align],
    max_width: Optional[int],
    max_empty_columns: int,
) -> Iterator[str]:
    if max_empty_columns:
        empty_pattern: Sequence[Any] = tuple([None]) * max_empty_columns

    for cells in zip_longest(
        *[
            _cell(field, width, align)
            for field, width, align in zip_longest(fields, widths, aligns)
        ]
    ):

        if max_empty_columns and cells[:max_empty_columns] == empty_pattern:
            continue
        line = "  ".join(
            cell or "".ljust(width or 0) for cell, width in zip_longest(cells, widths)
        )
        if max_width:
            line = StyledTextHelper.trim(line, max_width)
            yield line
        else:
            yield line


def _cell(val: str, width: int, align: Optional[Align]) -> Iterator[str]:
    if width <= 0:
        raise TypeError(f"Width must be positive integer")
    try:
        format_func = _align_to_format[align]
    except KeyError:
        raise ValueError(f"Unsupported align type: {align!r}")

    for sub in StyledTextHelper.wrap(val, width):
        yield format_func(sub, width)
