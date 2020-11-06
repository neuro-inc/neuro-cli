from typing import Any, List

import pytest
from dateutil.parser import isoparse

from neuromation.api import Disk
from neuromation.cli.formatters.disks import (
    DiskFormatter,
    DisksFormatter,
    SimpleDisksFormatter,
)


def test_disk_formatter(rich_cmp: Any) -> None:
    disk = Disk(
        "disk",
        int(11.93 * (1024 ** 3)),
        "user",
        Disk.Status.READY,
        "cluster",
        isoparse("2017-03-04T12:28:59.759433+00:00"),
        isoparse("2017-04-04T12:28:59.759433+00:00"),
    )
    fmtr = DiskFormatter(str)
    rich_cmp(fmtr(disk))


@pytest.fixture
def disks_list() -> List[Disk]:
    return [
        Disk(
            id="disk-1",
            storage=50 * (1024 ** 3),
            owner="user",
            status=Disk.Status.PENDING,
            cluster_name="cluster",
            created_at=isoparse("2017-03-04T12:28:59.759433+00:00"),
            last_usage=isoparse("2017-03-08T12:28:59.759433+00:00"),
        ),
        Disk(
            id="disk-2",
            storage=50 * (1024 ** 2),
            owner="user",
            status=Disk.Status.READY,
            cluster_name="cluster",
            created_at=isoparse("2017-04-04T12:28:59.759433+00:00"),
        ),
        Disk(
            id="disk-3",
            storage=50 * (1024 ** 1),
            owner="user",
            status=Disk.Status.READY,
            cluster_name="cluster",
            created_at=isoparse("2017-05-04T12:28:59.759433+00:00"),
        ),
        Disk(
            id="disk-4",
            storage=50,
            owner="user",
            status=Disk.Status.BROKEN,
            cluster_name="cluster",
            created_at=isoparse("2017-06-04T12:28:59.759433+00:00"),
        ),
    ]


def test_disks_formatter_simple(disks_list: List[Disk], rich_cmp: Any) -> None:
    fmtr = SimpleDisksFormatter()
    rich_cmp(fmtr(disks_list))


def test_disks_formatter_short(disks_list: List[Disk], rich_cmp: Any) -> None:
    fmtr = DisksFormatter(str)
    rich_cmp(fmtr(disks_list))


def test_disks_formatter_long(disks_list: List[Disk], rich_cmp: Any) -> None:
    fmtr = DisksFormatter(str, long_format=True)
    rich_cmp(fmtr(disks_list))
