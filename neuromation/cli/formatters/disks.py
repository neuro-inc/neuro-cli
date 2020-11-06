import abc
import operator
from typing import Sequence

from rich import box
from rich.console import RenderableType, RenderGroup
from rich.table import Table
from rich.text import Text

from neuromation.api import Disk
from neuromation.cli import utils
from neuromation.cli.formatters.jobs import format_datetime
from neuromation.cli.formatters.utils import URIFormatter


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
            line += [format_datetime(disk.created_at), format_datetime(disk.last_usage)]
        return line

    def __call__(self, disks: Sequence[Disk]) -> RenderableType:
        disks = sorted(disks, key=operator.attrgetter("id"))
        table = Table(box=box.SIMPLE_HEAVY)
        table.add_column("Id", style="bold")
        table.add_column("Storage")
        table.add_column("Uri")
        table.add_column("Status")
        if self._long_format:
            table.add_column("Created at")
            table.add_column("Last used")
        for disk in disks:
            table.add_row(*self._disk_to_table_row(disk))
        return table


class DiskFormatter:
    def __init__(self, uri_formatter: URIFormatter) -> None:
        self._disks_formatter = DisksFormatter(uri_formatter, long_format=True)

    def __call__(self, disk: Disk) -> RenderableType:
        return self._disks_formatter([disk])
