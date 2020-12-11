import abc
import operator
from datetime import timedelta
from typing import Optional, Sequence

from rich import box
from rich.console import RenderableType, RenderGroup
from rich.table import Table
from rich.text import Text

from neuro_sdk import Disk

from neuro_cli import utils
from neuro_cli.formatters.jobs import format_datetime, format_life_span
from neuro_cli.formatters.utils import URIFormatter


class BaseDisksFormatter:
    @abc.abstractmethod
    def __call__(self, jobs: Sequence[Disk]) -> RenderableType:
        pass


class SimpleDisksFormatter(BaseDisksFormatter):
    def __call__(self, disks: Sequence[Disk]) -> RenderableType:
        return RenderGroup(*[Text(disk.id) for disk in disks])


class DisksFormatter(BaseDisksFormatter):
    def __init__(
        self,
        uri_formatter: URIFormatter,
        *,
        long_format: bool = False,
    ) -> None:
        self._uri_formatter = uri_formatter
        self._long_format = long_format

    def _disk_to_table_row(self, disk: Disk) -> Sequence[str]:
        storage_str = utils.format_size(disk.storage)
        line = [disk.id, storage_str, self._uri_formatter(disk.uri), disk.status.value]
        if self._long_format:
            line += [
                format_datetime(disk.created_at),
                format_datetime(disk.last_usage),
                format_disk_life_span(disk.life_span),
            ]
        return line

    def __call__(self, disks: Sequence[Disk]) -> RenderableType:
        disks = sorted(disks, key=operator.attrgetter("id"))
        table = Table(box=box.SIMPLE_HEAVY)
        # make sure that the first column is fully expanded
        width = len("disk-06bed296-8b27-4aa8-9e2a-f3c47b41c807")
        table.add_column("Id", style="bold", width=width)
        table.add_column("Storage")
        table.add_column("Uri")
        table.add_column("Status")
        if self._long_format:
            table.add_column("Created at")
            table.add_column("Last used")
            table.add_column("Life span")
        for disk in disks:
            table.add_row(*self._disk_to_table_row(disk))
        return table


class DiskFormatter:
    def __init__(self, uri_formatter: URIFormatter) -> None:
        self._uri_formatter = uri_formatter

    def __call__(self, disk: Disk) -> RenderableType:
        table = Table(
            box=None,
            show_header=False,
            show_edge=False,
        )
        table.add_column()
        table.add_column(style="bold")
        table.add_row("Id", disk.id)
        table.add_row("Storage", utils.format_size(disk.storage))
        table.add_row("Uri", self._uri_formatter(disk.uri))
        table.add_row("Status", disk.status.value)
        table.add_row("Created at", format_datetime(disk.created_at))
        table.add_row("Last used", format_datetime(disk.last_usage))
        table.add_row("Life span", format_disk_life_span(disk.life_span))
        return table


def format_disk_life_span(life_span: Optional[timedelta]) -> str:
    if life_span is not None:
        return format_life_span(life_span.total_seconds())
    else:
        return format_life_span(None)
