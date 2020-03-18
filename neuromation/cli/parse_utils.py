import dataclasses
import re
from typing import Callable, List, Mapping, Optional, TypeVar

from .formatters.ftable import Align, ColumnWidth


_T = TypeVar("_T")


def parse_memory(memory: str) -> int:
    """Parse string expression i.e. 16M, 16MB, etc
    M = 1024 * 1024, MB = 1000 * 1000

    returns value in bytes"""

    # Mega, Giga, Tera, etc
    prefixes = "MGTPEZY"
    value_error = ValueError(f"Unable parse value: {memory}")

    if not memory:
        raise value_error

    pattern = r"^(?P<value>\d+)(?P<units>(kB|K)|((?P<prefix>[{prefixes}])(?P<unit>B?)))$".format(  # NOQA
        prefixes=prefixes
    )
    regex = re.compile(pattern)
    match = regex.fullmatch(memory)

    if not match:
        raise value_error

    groups = match.groupdict()

    value = int(groups["value"])
    unit = groups["unit"]
    prefix = groups["prefix"]
    units = groups["units"]

    if units == "kB":
        return value * 1000

    if units == "K":
        return value * 1024

    # Our prefix string starts with Mega
    # so for index 0 the power should be 2
    power = 2 + prefixes.index(prefix)
    multiple = 1000 if unit else 1024

    return value * multiple ** power


def to_megabytes(value: str) -> int:
    return int(parse_memory(value) / (1024 ** 2))


@dataclasses.dataclass(frozen=True)
class JobColumnInfo:
    id: str
    title: str
    align: Align
    width: ColumnWidth


# Note: please keep the help for format specs in sync with the following data
# structures.

COLUMNS = [
    JobColumnInfo("id", "ID", Align.LEFT, ColumnWidth()),
    JobColumnInfo("name", "NAME", Align.LEFT, ColumnWidth(max=40)),
    JobColumnInfo("tags", "TAGS", Align.LEFT, ColumnWidth(max=40)),
    JobColumnInfo("status", "STATUS", Align.LEFT, ColumnWidth(max=10)),
    JobColumnInfo("when", "WHEN", Align.LEFT, ColumnWidth(max=15)),
    JobColumnInfo("image", "IMAGE", Align.LEFT, ColumnWidth(max=40)),
    JobColumnInfo("owner", "OWNER", Align.LEFT, ColumnWidth(max=25)),
    JobColumnInfo("cluster_name", "CLUSTER", Align.LEFT, ColumnWidth(max=15)),
    JobColumnInfo("description", "DESCRIPTION", Align.LEFT, ColumnWidth(max=50)),
    JobColumnInfo("command", "COMMAND", Align.LEFT, ColumnWidth(max=100)),
]

COLUMNS_DEFAULT_IGNORE = {
    "tags",
}


def get_default_columns() -> List[JobColumnInfo]:
    return [col for col in COLUMNS if col.id not in COLUMNS_DEFAULT_IGNORE]


COLUMNS_MAP = {column.id: column for column in COLUMNS}

COLUMNS_RE = re.compile(
    r"""
    (?P<id>\w+)|
    (?:\{(?P<col>[^}]+)\})|
    (?P<sep>\s*(?:,\s*|\s))|
    (?P<miss>.)
    """,
    re.VERBOSE,
)
COLUMN_RE = re.compile(
    r"""
    (?P<id>\w+)
    (?:
      (?:;align=(?P<align>\w+))|
      (?:;min=(?P<min>\w+))|
      (?:;max=(?P<max>\w+))|
      (?:;width=(?P<width>\w+))
    )*
    (?:;(?P<title>.+))?
    """,
    re.VERBOSE,
)


def _get(
    dct: Mapping[str, Optional[str]],
    name: str,
    fmt: str,
    converter: Callable[[str], _T],
    default: Optional[_T],
) -> Optional[_T]:
    val = dct[name]
    if val is None:
        return default
    else:
        try:
            return converter(val)
        except ValueError:
            raise ValueError(f"Invalid property {name}: {val!r} of format {fmt!r}")


def parse_columns(fmt: Optional[str]) -> List[JobColumnInfo]:
    # Column format is "{id[;field=val][;title]}",
    # columns are separated by commas or spaces
    # spaces in title are forbidden
    if not fmt:
        return get_default_columns()
    ret = []
    for m1 in COLUMNS_RE.finditer(fmt):
        if m1.lastgroup == "sep":
            continue
        elif m1.lastgroup == "miss":
            raise ValueError(f"Invalid format {fmt!r}")
        elif m1.lastgroup == "col":
            column = m1.group("col")
        elif m1.lastgroup == "id":
            column = m1.group("id")
        else:
            continue
        m2 = COLUMN_RE.fullmatch(column)
        if m2 is None:
            raise ValueError(f"Invalid format {fmt!r}")
        groups = m2.groupdict()
        id = groups["id"].lower()
        default = COLUMNS_MAP.get(id)
        if default is None:
            for name in COLUMNS_MAP:
                if name.startswith(id):
                    if default is not None:
                        variants = ", ".join(
                            name for name in COLUMNS_MAP if name.startswith(id)
                        )
                        raise ValueError(
                            f"Ambiguous column {id!r} in format {fmt!r};"
                            f" available variants: {variants}"
                        )
                    default = COLUMNS_MAP[name]
            if default is None:
                raise ValueError(f"Unknown column {id!r} in format {fmt!r}")
        title = _get(groups, "title", fmt, str, default.title)
        assert title is not None
        align = _get(groups, "align", fmt, Align, default.align)
        assert align is not None

        width_min = _get(groups, "min", fmt, int, None)
        width_max = _get(groups, "max", fmt, int, None)
        if width_max is not None:
            if width_min is not None and width_min > width_max:
                width_min = width_max
        else:
            if (
                width_min is not None
                and default.width.max is not None
                and default.width.max < width_min
            ):
                width_max = width_min
            else:
                width_max = default.width.max

        width = _get(groups, "width", fmt, int, None)
        if width is not None:
            width_min = width_max = width

        info = JobColumnInfo(
            id=default.id,  # canonical name
            title=title,
            align=align,
            width=ColumnWidth(width_min, width_max, width),
        )
        ret.append(info)
    if not ret:
        raise ValueError(f"Invalid format {fmt!r}")
    return ret
