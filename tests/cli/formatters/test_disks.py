import textwrap
from typing import List

import click
import pytest
from dateutil.parser import isoparse

from neuromation.api import Disk
from neuromation.cli.formatters.disks import (
    DiskFormatter,
    DisksFormatter,
    SimpleDisksFormatter,
)


def test_disk_formatter() -> None:
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
    result = "\n".join(click.unstyle(line).rstrip() for line in fmtr(disk))
    assert result == textwrap.dedent(
        f"""\
        Id    Storage  Uri                       Status  Created at   Last used
        disk  11.9G    disk://cluster/user/disk  Ready   Mar 04 2017  Apr 04 2017"""
    )


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


def test_disks_formatter_simple(disks_list: List[Disk]) -> None:
    fmtr = SimpleDisksFormatter()
    result = "\n".join(click.unstyle(line).rstrip() for line in fmtr(disks_list))
    assert result == textwrap.dedent(
        f"""\
        disk-1
        disk-2
        disk-3
        disk-4"""
    )


def test_disks_formatter_short(disks_list: List[Disk]) -> None:
    fmtr = DisksFormatter(str)
    result = "\n".join(click.unstyle(line).rstrip() for line in fmtr(disks_list))
    assert result == textwrap.dedent(
        f"""\
        Id      Storage  Uri                         Status
        disk-1  50.0G    disk://cluster/user/disk-1  Pending
        disk-2  50.0M    disk://cluster/user/disk-2  Ready
        disk-3  50.0K    disk://cluster/user/disk-3  Ready
        disk-4  50B      disk://cluster/user/disk-4  Broken"""
    )


def test_disks_formatter_long(disks_list: List[Disk]) -> None:
    fmtr = DisksFormatter(str, long_format=True)
    result = "\n".join(click.unstyle(line).rstrip() for line in fmtr(disks_list))
    assert result == textwrap.dedent(
        f"""\
        Id      Storage  Uri                         Status   Created at   Last used
        disk-1  50.0G    disk://cluster/user/disk-1  Pending  Mar 04 2017  Mar 08 2017
        disk-2  50.0M    disk://cluster/user/disk-2  Ready    Apr 04 2017
        disk-3  50.0K    disk://cluster/user/disk-3  Ready    May 04 2017
        disk-4  50B      disk://cluster/user/disk-4  Broken   Jun 04 2017"""
    )
