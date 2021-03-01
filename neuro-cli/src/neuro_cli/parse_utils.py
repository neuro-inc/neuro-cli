import dataclasses
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple, TypeVar

import click
from rich.console import JustifyMethod

from neuro_sdk import JobDescription, JobStatus, JobTelemetry

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

    pattern = r"^(?P<value>\d+)(?P<units>(kB|kb|K|k)|((?P<prefix>[{prefixes}])(?P<unit>[bB]?)))$".format(  # NOQA
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

    if units == "kB" or units == "kb":
        return value * 1000

    if units == "K" or units == "k":
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
    justify: JustifyMethod = "default"
    width: Optional[int] = None
    min_width: Optional[int] = None
    max_width: Optional[int] = None


# Note: please keep the help for format specs in sync with the following data
# structures.

PS_COLUMNS = [
    JobColumnInfo(
        "id", "ID", "left", width=len("job-28040560-2a21-428e-a7c0-44c809490b53")
    ),
    JobColumnInfo("name", "NAME", "left", max_width=40),
    JobColumnInfo("tags", "TAGS", "left", max_width=40),
    JobColumnInfo("status", "STATUS", "left", max_width=10),
    JobColumnInfo("when", "WHEN", "left", max_width=32),
    JobColumnInfo("created", "CREATED", "left", max_width=15),
    JobColumnInfo("started", "STARTED", "left", max_width=15),
    JobColumnInfo("finished", "FINISHED", "left", max_width=15),
    JobColumnInfo("image", "IMAGE", "left", max_width=40),
    JobColumnInfo("owner", "OWNER", "left", max_width=25),
    JobColumnInfo("cluster_name", "CLUSTER", "left", max_width=15),
    JobColumnInfo("description", "DESCRIPTION", "left", max_width=50),
    JobColumnInfo("command", "COMMAND", "left", max_width=100),
    JobColumnInfo("life_span", "LIFE-SPAN", "left"),
    JobColumnInfo("workdir", "WORKDIR", "left"),
    JobColumnInfo("preset", "PRESET", "left"),
]

PS_COLUMNS_DEFAULT_IGNORE = {
    "tags",
    "life_span",
    "created",
    "started",
    "finished",
    "cluster_name",
    "description",
    "workdir",
    "preset",
}

PS_COLUMNS_DEFAULT = {
    col.id for col in PS_COLUMNS if col.id not in PS_COLUMNS_DEFAULT_IGNORE
}

TOP_COLUMNS = PS_COLUMNS + [
    JobColumnInfo("cpu", "CPU", "right", width=15),
    JobColumnInfo("memory", "MEMORY (MB)", "right", width=15),
    JobColumnInfo("gpu", "GPU (%)", "right", width=15),
    JobColumnInfo("gpu_memory", "GPU_MEMORY (MB)", "right", width=15),
]

TOP_COLUMNS_DEFAULT = {
    "id",
    "when",
    "cpu",
    "memory",
    "gpu",
    "gpu_memory",
}


def get_default_ps_columns() -> List[JobColumnInfo]:
    return [col for col in PS_COLUMNS if col.id in PS_COLUMNS_DEFAULT]


def get_default_top_columns() -> List[JobColumnInfo]:
    return [col for col in TOP_COLUMNS if col.id in TOP_COLUMNS_DEFAULT]


PS_COLUMNS_MAP = {column.id: column for column in PS_COLUMNS}
TOP_COLUMNS_MAP = {column.id: column for column in TOP_COLUMNS}

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


def _justify(arg: str) -> JustifyMethod:
    ALLOWED = ("left", "right", "center", "full")
    if arg not in ALLOWED:
        raise ValueError(f"Unknown align {arg}, allowed {ALLOWED}")
    return arg  # type: ignore


def parse_ps_columns(fmt: Optional[str]) -> List[JobColumnInfo]:
    return _parse_columns(fmt, PS_COLUMNS_MAP) or get_default_ps_columns()


def parse_top_columns(fmt: Optional[str]) -> List[JobColumnInfo]:
    return _parse_columns(fmt, TOP_COLUMNS_MAP) or get_default_top_columns()


def _parse_columns(
    fmt: Optional[str], columns_map: Dict[str, JobColumnInfo]
) -> Optional[List[JobColumnInfo]]:
    # Column format is "{id[;field=val][;title]}",
    # columns are separated by commas or spaces
    # spaces in title are forbidden
    if not fmt:
        return None
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
        default = columns_map.get(id)
        if default is None:
            for name in columns_map:
                if name.startswith(id):
                    if default is not None:
                        variants = ", ".join(
                            name for name in columns_map if name.startswith(id)
                        )
                        raise ValueError(
                            f"Ambiguous column {id!r} in format {fmt!r};"
                            f" available variants: {variants}"
                        )
                    default = columns_map[name]
            if default is None:
                raise ValueError(f"Unknown column {id!r} in format {fmt!r}")
        title = _get(groups, "title", fmt, str, default.title)
        assert title is not None

        justify: JustifyMethod = _get(groups, "align", fmt, _justify, default.justify)  # type: ignore  # noqa

        min_width = _get(groups, "min", fmt, int, default.min_width)
        max_width = _get(groups, "max", fmt, int, default.max_width)
        width = _get(groups, "width", fmt, int, default.width)

        info = JobColumnInfo(
            id=default.id,  # canonical name
            title=title,
            justify=justify,
            width=width,
            min_width=min_width,
            max_width=max_width,
        )
        ret.append(info)
    if not ret:
        raise ValueError(f"Invalid format {fmt!r}")
    return ret


class InvertKey:
    def __init__(self, value: Any) -> None:
        self.value = Any

    def __lt__(self, other: Any) -> Any:
        return self.value > other.value

    def __gt__(self, other: Any) -> Any:
        return self.value < other.value

    def __le__(self, other: Any) -> Any:
        return self.value >= other.value

    def __ge__(self, other: Any) -> Any:
        return self.value <= other.value

    def __eq__(self, other: Any) -> Any:
        return self.value == other.value

    def __ne__(self, other: Any) -> Any:
        return self.value != other.value


JobTelemetryKeyFunc = Callable[[Tuple[JobDescription, JobTelemetry]], Any]

JOB_STATUS_PRIORITIES = {status: i for i, status in enumerate(JobStatus)}
DATETIME_MIN = datetime.min.replace(tzinfo=timezone.utc)
INF = float("inf")

SORT_KEY_FUNCS: Dict[str, JobTelemetryKeyFunc] = {
    # JobDescriptor attibutes
    "id": lambda item: item[0].id,
    "name": lambda item: item[0].name or "",
    "status": lambda item: JOB_STATUS_PRIORITIES[item[0].status],
    "created": lambda item: item[0].history.created_at or DATETIME_MIN,
    "started": lambda item: item[0].history.started_at or DATETIME_MIN,
    "finished": lambda item: item[0].history.finished_at or DATETIME_MIN,
    "when": lambda item: item[0].history.changed_at,
    "image": lambda item: str(item[0].container.image),
    "owner": lambda item: item[0].owner,
    "description": lambda item: item[0].description or "",
    "cluster_name": lambda item: item[0].cluster_name,
    "command": lambda item: item[0].container.command,
    "life_span": lambda item: item[0].life_span or INF,
    "workdir": lambda item: item[0].container.working_dir or "",
    "preset": lambda item: item[0].preset_name or "",
    # JobTelemetry attibutes
    "cpu": lambda item: -item[1].cpu,
    "memory": lambda item: -item[1].memory,
    "gpu": lambda item: -(item[1].gpu_duty_cycle or 0),
    "gpu_memory": lambda item: -(item[1].gpu_memory or 0),
}

SORT_KEY_NAMES = tuple(SORT_KEY_FUNCS)


def parse_sort_keys(fmt: str) -> List[Tuple[JobTelemetryKeyFunc, bool]]:
    sort_keys: List[Tuple[JobTelemetryKeyFunc, bool]] = []
    for keyname in fmt.split(","):
        keyname = keyname.strip()
        if keyname[:1] == "-":
            reverse = True
            keyname = keyname[1:]
        else:
            reverse = False

        try:
            keyfunc = SORT_KEY_FUNCS[keyname]
        except KeyError:
            raise ValueError(f"invalid sort key {keyname!r}") from None
        sort_keys.append((keyfunc, reverse))

    return sort_keys


REGEX_TIME_DELTA = re.compile(
    r"^((?P<d>\d+)d)?((?P<h>\d+)h)?((?P<m>\d+)m)?((?P<s>\d+)s)?$"
)


def parse_timedelta(value: str) -> timedelta:
    value = value.strip()
    err = f"Could not parse time delta '{value}'"
    if value == "":
        raise click.UsageError(f"{err}: Empty string not allowed")
    if value == "0":
        return timedelta(0)
    match = REGEX_TIME_DELTA.search(value)
    if match is None:
        raise click.UsageError(
            f"{err}: Should be like '1d2h3m4s' (some parts may be missing)."
        )
    return timedelta(
        days=int(match.group("d") or 0),
        hours=int(match.group("h") or 0),
        minutes=int(match.group("m") or 0),
        seconds=int(match.group("s") or 0),
    )


# Opposite to function above
def serialize_timedelta(value: timedelta) -> str:
    res = ""
    total_seconds = int(value.total_seconds())
    hours = total_seconds // 3600 % 24
    minutes = total_seconds // 60 % 60
    seconds = total_seconds % 60
    if value.days:
        res += f"{value.days}d"
    if hours:
        res += f"{hours}h"
    if minutes:
        res += f"{minutes}m"
    if seconds:
        res += f"{seconds}s"
    if res == "":
        res = "0"
    return res
