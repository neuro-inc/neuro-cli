from enum import Enum
from itertools import zip_longest
from textwrap import wrap
from typing import Any, Iterator, List, Optional, Sequence, Union


__all__ = ["table"]
__version__ = "0.1"


class Align(str, Enum):
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"


def table(
    rows: Sequence[Sequence[str]],
    widths: Sequence[Optional[Union[int, range]]] = (),
    aligns: Sequence[Align] = (),
    max_width: Optional[int] = None,
) -> Iterator[str]:

    # Columns widths calculation
    if len(widths) < len(rows[0]):
        widths = tuple(widths) + tuple([None]) * (len(rows[0]) - len(widths))
    calc_widths: List[int] = []
    for i in range(len(widths)):
        width = widths[i]
        if isinstance(width, int):
            calc_widths.append(width)
            continue
        max_cell_width: int = max(len(row[i]) for row in rows)
        if width is None:
            calc_widths.append(max_cell_width)
        elif isinstance(width, range):
            if max_cell_width in width:
                calc_widths.append(max_cell_width)
            else:
                calc_widths.append(width[-1])
        else:
            raise TypeError(f"Unsopported width[{i}]: {width!r}")

    # How many empty columns can be displayed
    max_empty_columns = len(rows[0])
    if max_width:
        for i in range(len(widths)):
            if sum(calc_widths[0 : (i + 1)]) > max_width:
                max_empty_columns = i
                break

    for row in rows:
        for line in _row(row, calc_widths, aligns, max_width, max_empty_columns):
            yield line
    pass


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
    if width <= 0:
        raise TypeError(f"Width must be positive integer")
    else:
        if align == Align.LEFT or align is None:
            format_func = "ljust"
        elif align == Align.RIGHT:
            format_func = "rjust"
        elif align == Align.CENTER:
            format_func = "center"
        else:
            raise ValueError(f"Unsupported align type: {align}")

        for sub in wrap(val, width):
            yield getattr(sub, format_func)(width)
