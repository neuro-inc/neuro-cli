from typing import Iterator, Sequence

import click

from neuromation.api import Disk
from neuromation.cli.formatters.ftable import table
from neuromation.cli.formatters.utils import URIFormatter


class DisksFormatter:
    _table_header = [
        click.style("Id", bold=True),
        click.style("Storage", bold=True),
        click.style("Uri", bold=True),
        click.style("Status", bold=True),
    ]

    def __init__(self, uri_formatter: URIFormatter):
        self._uri_formatter = uri_formatter

    def _disk_to_table_row(self, disk: Disk) -> Sequence[str]:
        if disk.storage >= 1024 ** 3:
            storage_str = f"{disk.storage / (1024 ** 3):.2f}G"
        elif disk.storage >= 1024 ** 2:
            storage_str = f"{disk.storage / (1024 ** 2):.2f}M"
        elif disk.storage >= 1024:
            storage_str = f"{disk.storage / 1024:.2f}K"
        else:
            storage_str = str(disk.storage)
        return [disk.id, storage_str, self._uri_formatter(disk.uri), disk.status.value]

    def __call__(self, disks: Sequence[Disk]) -> Iterator[str]:
        disks_info = [
            self._table_header,
            *(self._disk_to_table_row(disk) for disk in disks),
        ]
        return table(disks_info)


class DiskFormatter:
    def __init__(self, uri_formatter: URIFormatter):
        self._disks_formatter = DisksFormatter(uri_formatter)

    def __call__(self, disk: Disk) -> Iterator[str]:
        return self._disks_formatter([disk])
