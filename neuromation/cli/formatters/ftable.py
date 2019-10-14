from dataclasses import dataclass
from enum import Enum
from itertools import zip_longest
from textwrap import wrap
from typing import Any, Iterator, List, Optional, Sequence, Union


__all__ = ["table"]
__version__ = "0.1"


@dataclass
class ColumnWidth:
    min: Optional[int] = None
    max: Optional[int] = None

    def __post_init__(self) -> None:
        assert not self.min or self.min > 0
        assert not self.max or self.max > 0


class Align(str, Enum):
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"


_align_to_format = {
    Align.LEFT: str.ljust,
    Align.RIGHT: str.rjust,
    Align.CENTER: str.center,
    None: str.ljust,
}


def table(
    rows: Sequence[Sequence[str]],
    widths: Sequence[Optional[Union[int, ColumnWidth]]] = (),
    aligns: Sequence[Align] = (),
    max_width: Optional[int] = None,
) -> Iterator[str]:

    # Columns widths calculation
    if len(widths) < len(rows[0]):
        widths = tuple(widths) + tuple([None]) * (len(rows[0]) - len(widths))
    calc_widths: List[int] = []
    for i, width in enumerate(widths):
        if isinstance(width, int):
            calc_widths.append(width)
            continue
        max_cell_width: int = max(len(row[i]) for row in rows)
        if width is None:
            calc_widths.append(max_cell_width)
        elif isinstance(width, ColumnWidth):
            if (not width.min or width.min <= max_cell_width) and (
                not width.max or width.max >= max_cell_width
            ):
                calc_widths.append(max_cell_width)
            elif width.max:
                calc_widths.append(width.max)
            else:
                calc_widths.append(max_cell_width)
        else:
            raise TypeError(f"Unsopported width[{i}]: {widths[i]}")

    # How many empty columns can be displayed
    max_empty_columns = len(rows[0])
    if max_width:
        sum_width = 0
        for i, width in enumerate(calc_widths):
            sum_width += width
            if sum_width > max_width:
                max_empty_columns = i
                break

    for row in rows:
        for line in _row(row, calc_widths, aligns, max_width, max_empty_columns):
            yield line


def _row(
    fields: Sequence[str],
    widths: Sequence[int],
    aligns: Sequence[Align] = None,
    max_width: Optional[int] = None,
    max_empty_columns: Optional[int] = None,
) -> Iterator[str]:
    if aligns is None:
        aligns = []

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
            cell if cell else "".ljust(width) if width else ""
            for cell, width in zip_longest(cells, widths)
        )
        if max_width:
            yield line[:max_width]
        else:
            yield line


def _cell(val: str, width: int, align: Optional[Align] = Align.LEFT) -> Iterator[str]:
    if not width or width <= 0:
        raise TypeError(f"Width must be positive integer")
    try:
        format_func = _align_to_format[align]
    except KeyError:
        raise ValueError(f"Unsupported align type: {align!r}")
    for sub in wrap(val, width):
        yield format_func(sub, width)
