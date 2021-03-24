import datetime
from typing import Callable, Optional, overload

import humanize
from typing_extensions import Protocol
from yarl import URL

from neuro_sdk import RemoteImage
from neuro_sdk.url_utils import CLUSTER_SCHEMES

URIFormatter = Callable[[URL], str]
ImageFormatter = Callable[[RemoteImage], str]


def uri_formatter(username: str, cluster_name: str) -> URIFormatter:
    def formatter(uri: URL) -> str:
        if uri.scheme in CLUSTER_SCHEMES:
            if uri.host == cluster_name:
                assert uri.path[0] == "/"
                path = uri.path.lstrip("/")
                owner, _, rest = path.partition("/")
                if owner == username:
                    return f"{uri.scheme}:{rest.lstrip('/')}"
                return f"{uri.scheme}:/{path}"
        return str(uri)

    return formatter


def image_formatter(uri_formatter: URIFormatter) -> ImageFormatter:
    def formatter(image: RemoteImage) -> str:
        image_str = str(image)
        if image_str.startswith("image://"):
            return uri_formatter(URL(image_str))
        else:
            return image_str

    return formatter


def format_timedelta(delta: datetime.timedelta) -> str:
    s = int(delta.total_seconds())
    if s < 0:
        raise ValueError(f"Invalid delta {delta}: expect non-negative total value")
    _sec_in_minute = 60
    _sec_in_hour = _sec_in_minute * 60
    _sec_in_day = _sec_in_hour * 24
    d, s = divmod(s, _sec_in_day)
    h, s = divmod(s, _sec_in_hour)
    m, s = divmod(s, _sec_in_minute)
    return "".join(
        [
            f"{d}d" if d else "",
            f"{h}h" if h else "",
            f"{m}m" if m else "",
            f"{s}s" if s else "",
        ]
    )


def format_datetime_iso(
    when: Optional[datetime.datetime], *, precise: bool = False
) -> str:
    if when is None:
        return ""
    return when.isoformat()


def format_datetime_human(
    when: Optional[datetime.datetime],
    *,
    precise: bool = False,
    timezone: Optional[datetime.timezone] = None,
) -> str:
    """Humanizes the datetime

    When not in precise mode (precise=False), prints number of largest units
    for moments that are less then a day ago, and date just day otherwise:

    "32 seconds ago"
    "5 minutes ago"
    "11 hours age"
    "yesterday"
    "Jan 1"

    In precise mode (precise=True), prints two largest units for moments
    that are less then a day ago, and date with time otherwise:

    "32 seconds ago"
    "5 minutes and 22 seconds ago"
    "5 hours and 31 minutes ago"
    "yesterday at 14:22"
    "Jan 1 at 00:01"
    """
    if when is None:
        return ""
    assert when.tzinfo is not None
    delta = datetime.datetime.now(datetime.timezone.utc) - when
    if delta < datetime.timedelta(days=1):
        if precise:
            min_unit = "seconds"
            if delta > datetime.timedelta(hours=1):
                min_unit = "minutes"
            return (
                humanize.precisedelta(delta, minimum_unit=min_unit, format="%0.0f")
                + " ago"
            )
        return humanize.naturaltime(delta)
    else:
        when_local = when.astimezone(timezone)
        result = humanize.naturaldate(when_local)
        if precise:
            result = f"{result} at {when_local.strftime('%H:%M')} "
        return result


class DatetimeFormatter(Protocol):
    @overload
    def __call__(self, when: Optional[datetime.datetime]) -> str:
        ...

    @overload
    def __call__(self, when: Optional[datetime.datetime], *, precise: bool) -> str:
        ...

    def __call__(
        self, when: Optional[datetime.datetime], *, precise: bool = True
    ) -> str:
        ...


def get_datetime_formatter(use_iso_format: bool) -> DatetimeFormatter:
    if use_iso_format:
        return format_datetime_iso
    return format_datetime_human


def yes() -> str:
    return "[green]√[/green]"


def no() -> str:
    return "[red]×[/red]"
