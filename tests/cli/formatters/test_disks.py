import textwrap

import click
from dateutil.parser import isoparse

from neuromation.api import Disk
from neuromation.cli.formatters.disks import DiskFormatter, DisksFormatter


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


def test_disks_formatter_short() -> None:
    disks = [
        Disk(
            "disk-1",
            50 * (1024 ** 3),
            "user",
            Disk.Status.PENDING,
            "cluster",
            isoparse("2017-03-04T12:28:59.759433+00:00"),
        ),
        Disk(
            "disk-2",
            50 * (1024 ** 2),
            "user",
            Disk.Status.READY,
            "cluster",
            isoparse("2017-04-04T12:28:59.759433+00:00"),
        ),
        Disk(
            "disk-3",
            50 * (1024 ** 1),
            "user",
            Disk.Status.READY,
            "cluster",
            isoparse("2017-05-04T12:28:59.759433+00:00"),
        ),
        Disk(
            "disk-4",
            50,
            "user",
            Disk.Status.READY,
            "cluster",
            isoparse("2017-06-04T12:28:59.759433+00:00"),
        ),
    ]
    fmtr = DisksFormatter(str)
    result = "\n".join(click.unstyle(line).rstrip() for line in fmtr(disks))
    assert result == textwrap.dedent(
        f"""\
        Id      Storage  Uri                         Status
        disk-1  50.0G    disk://cluster/user/disk-1  Pending
        disk-2  50.0M    disk://cluster/user/disk-2  Ready
        disk-3  50.0K    disk://cluster/user/disk-3  Ready
        disk-4  50B      disk://cluster/user/disk-4  Ready"""
    )


def test_disks_formatter_long() -> None:
    disks = [
        Disk(
            "disk-1",
            50 * (1024 ** 3),
            "user",
            Disk.Status.PENDING,
            "cluster",
            isoparse("2017-03-04T12:28:59.759433+00:00"),
            isoparse("2017-03-08T12:28:59.759433+00:00"),
        ),
        Disk(
            "disk-2",
            50 * (1024 ** 2),
            "user",
            Disk.Status.READY,
            "cluster",
            isoparse("2017-04-04T12:28:59.759433+00:00"),
        ),
        Disk(
            "disk-3",
            50 * (1024 ** 1),
            "user",
            Disk.Status.READY,
            "cluster",
            isoparse("2017-05-04T12:28:59.759433+00:00"),
        ),
        Disk(
            "disk-4",
            50,
            "user",
            Disk.Status.READY,
            "cluster",
            isoparse("2017-06-04T12:28:59.759433+00:00"),
        ),
    ]
    fmtr = DisksFormatter(str, long_format=True)
    result = "\n".join(click.unstyle(line).rstrip() for line in fmtr(disks))
    assert result == textwrap.dedent(
        f"""\
        Id      Storage  Uri                         Status   Created at   Last used
        disk-1  50.0G    disk://cluster/user/disk-1  Pending  Mar 04 2017  Mar 08 2017
        disk-2  50.0M    disk://cluster/user/disk-2  Ready    Apr 04 2017
        disk-3  50.0K    disk://cluster/user/disk-3  Ready    May 04 2017
        disk-4  50B      disk://cluster/user/disk-4  Ready    Jun 04 2017"""
    )
