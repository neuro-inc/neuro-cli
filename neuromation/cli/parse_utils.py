import dataclasses
import re
from typing import Callable, Dict, List, Optional, TypeVar

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


COLUMNS = [
    JobColumnInfo("id", "ID", Align.LEFT, ColumnWidth()),
    JobColumnInfo("name", "NAME", Align.LEFT, ColumnWidth(max=20)),
    JobColumnInfo("status", "STATUS", Align.LEFT, ColumnWidth(max=10)),
    JobColumnInfo("when", "WHEN", Align.LEFT, ColumnWidth(max=15)),
    JobColumnInfo("image", "IMAGE", Align.LEFT, ColumnWidth(max=40)),
    JobColumnInfo("owner", "OWNER", Align.LEFT, ColumnWidth(max=25)),
    JobColumnInfo("cluster_name", "CLUSTER", Align.LEFT, ColumnWidth(max=15)),
    JobColumnInfo("description", "DESCRIPTION", Align.LEFT, ColumnWidth(max=50)),
    JobColumnInfo("command", "COMMAND", Align.LEFT, ColumnWidth(max=100)),
]

COLUMNS_MAP = {column.id: column for column in COLUMNS}

COLUMNS_RE = re.compile(
    r"""
    (?P<col>(\{[^}]+)\})|
    (?P<sep>\s*(?:,\s*)?)|
    (?P<miss>.)
    """,
    re.VERBOSE,
)
COLUMN_RE = re.compile(
    r"""
    \A
    (?P<id>\w+)
    (?:
      (?:;align=(?P<align>\w+))|
      (?:;min=(?P<min>\w+))|
      (?:;max=(?P<max>\w+))|
      (?:;width=(?P<width>\w+))
    )*
    (?:;(?P<title>.+))?
    \Z
    """,
    re.VERBOSE,
)


def _get(
    dct: Dict[str, Optional[str]],
    name: str,
    fmt: str,
    converter: Callable[[str], _T],
    default: _T,
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
        return COLUMNS
    ret = []
    for m1 in COLUMNS_RE.finditer(fmt):
        if m1.lastgroup == "sep":
            continue
        elif m1.lastgroup == "miss":
            raise ValueError(f"Invalid format {fmt!r}")
        column = m1.group()[1:-1]
        m2 = COLUMN_RE.match(column)
        if m2 is None:
            raise ValueError(f"Invalid format {fmt!r}")
        groups = m2.groupdict()
        id = groups["id"]
        if id not in COLUMNS_MAP:
            raise ValueError(f"Unknown column {id!r} of format {fmt!r}")
        default = COLUMNS_MAP[id]
        info = JobColumnInfo(
            id=id,
            title=_get(groups, "title", fmt, str, default.title),
            align=_get(groups, "align", fmt, Align, default.align),
            width=ColumnWidth(
                _get(groups, "min", fmt, int, default.width.min),
                _get(groups, "max", fmt, int, default.width.max),
                _get(groups, "width", fmt, int, default.width.width),
            ),
        )
        ret.append(info)
    return ret
