import dataclasses
import re
from typing import List, Optional

from .formatters.ftable import Align, ColumnWidth


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

COLUMNS_SPLIT_RE = re.compile(r"(?:\s*,+\s*)|(?:\s+)")
COLUMN_RE = re.compile(
    r"""
    \A\{
    (?P<id>\w+)
    (?:
      (?:;align=(?P<align>\w+))|
      (?:;min=(?P<min>\d+))|
      (?:;max=(?P<max>\d+))|
      (?:;width=(?P<width>\d+))
    )*
    (?:;(?P<title>[^}]+))?
    \}\Z
    """,
    re.VERBOSE,
)


def parse_columns(fmt: Optional[str]) -> List[JobColumnInfo]:
    # Column format is "{id[;field=val][;title]}",
    # columns are separated by commas or spaces
    if not fmt:
        return COLUMNS
    columns = COLUMNS_SPLIT_RE.split(fmt)
    ret = []
    for column in columns:
        m = COLUMN_RE.match(column)
        if m is None:
            raise ValueError(f"Invalid format string {fmt!r}")
        groups = m.groupdict()
        id = groups["id"]
        if id not in COLUMNS_MAP:
            raise ValueError(f"Unknown column {id}")
        default = COLUMNS_MAP[id]
        title = groups.get("title", default.title)
        align = Align(groups.get("align", default.align))
        mins = groups.get("min", default.width.min)
        maxs = groups.get("min", default.width.max)
        widths = groups.get("min", default.width.width)
        info = JobColumnInfo(
            id=id,
            title=title,
            align=align,
            width=ColumnWidth(
                int(mins) if mins is not None else None,
                int(maxs) if maxs is not None else None,
                int(widths) if widths is not None else None,
            ),
        )
        ret.append(info)
    return ret
