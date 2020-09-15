import abc
from typing import Iterator, Sequence

import click

from neuromation.api import Disk
from neuromation.cli import utils
from neuromation.cli.formatters.ftable import table
from neuromation.cli.formatters.jobs import format_datetime
from neuromation.cli.formatters.utils import URIFormatter


class BaseDisksFormatter:
    @abc.abstractmethod
    def __call__(self, jobs: Sequence[Disk]) -> Iterator[str]:  # pragma: no cover
        pass


class SimpleDisksFormatter(BaseDisksFormatter):
    def __call__(self, disks: Sequence[Disk]) -> Iterator[str]:
        for disk in disks:
            yield disk.id


class DisksFormatter(BaseDisksFormatter):
    _table_header_short = [
        click.style("Id", bold=True),
        click.style("Storage", bold=True),
        click.style("Uri", bold=True),
        click.style("Status", bold=True),
    ]

    _table_header_long = _table_header_short + [
        click.style("Created at", bold=True),
        click.style("Last used", bold=True),
    ]

    def __init__(self, uri_formatter: URIFormatter, *, long_format: bool = False):
        self._uri_formatter = uri_formatter
        self._long_format = long_format

    def _disk_to_table_row(self, disk: Disk) -> Sequence[str]:
        storage_str = utils.format_size(disk.storage)
        line = [disk.id, storage_str, self._uri_formatter(disk.uri), disk.status.value]
        if self._long_format:
            line += [format_datetime(disk.created_at), format_datetime(disk.last_usage)]
        return line

    def __call__(self, disks: Sequence[Disk]) -> Iterator[str]:
        disks_info = [
            self._table_header_long if self._long_format else self._table_header_short,
            *(self._disk_to_table_row(disk) for disk in disks),
        ]
        return table(disks_info)


class DiskFormatter:
    def __init__(self, uri_formatter: URIFormatter):
        self._disks_formatter = DisksFormatter(uri_formatter, long_format=True)

    def __call__(self, disk: Disk) -> Iterator[str]:
        return self._disks_formatter([disk])
