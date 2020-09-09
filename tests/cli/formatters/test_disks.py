import click

from neuromation.api import Disk
from neuromation.cli.formatters.disks import DiskFormatter, DisksFormatter


def test_disk_formatter() -> None:
    disk = Disk("disk", int(11.93 * (1024 ** 3)), "user", Disk.Status.READY, "cluster")
    fmtr = DiskFormatter(str)
    header_line, info_line = (click.unstyle(line).rstrip() for line in fmtr(disk))
    assert header_line.split() == ["Id", "Storage", "Uri", "Status"]
    assert info_line.split() == ["disk", "11.9G", "disk://cluster/user/disk", "Ready"]


def test_disks_formatter() -> None:
    disks = [
        Disk("disk-1", 50 * (1024 ** 3), "user", Disk.Status.PENDING, "cluster"),
        Disk("disk-2", 50 * (1024 ** 2), "user", Disk.Status.READY, "cluster"),
        Disk("disk-3", 50 * (1024 ** 1), "user", Disk.Status.READY, "cluster"),
        Disk("disk-4", 50, "user", Disk.Status.READY, "cluster"),
    ]
    fmtr = DisksFormatter(str)
    header_line, *info_lines = (click.unstyle(line).rstrip() for line in fmtr(disks))
    assert header_line.split() == ["Id", "Storage", "Uri", "Status"]
    assert info_lines[0].split() == [
        "disk-1",
        "50.0G",
        "disk://cluster/user/disk-1",
        "Pending",
    ]
    assert info_lines[1].split() == [
        "disk-2",
        "50.0M",
        "disk://cluster/user/disk-2",
        "Ready",
    ]
    assert info_lines[2].split() == [
        "disk-3",
        "50.0K",
        "disk://cluster/user/disk-3",
        "Ready",
    ]
    assert info_lines[3].split() == [
        "disk-4",
        "50B",
        "disk://cluster/user/disk-4",
        "Ready",
    ]
