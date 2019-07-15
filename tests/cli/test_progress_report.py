import sys
from typing import Any

from yarl import URL

from neuromation.api import (
    StorageProgressComplete,
    StorageProgressFail,
    StorageProgressMkdir,
    StorageProgressStart,
    StorageProgressStep,
)
from neuromation.cli.command_progress_report import (
    ProgressBase,
    StandardPrintPercentOnly,
)


def test_progress_factory_none() -> None:
    progress = ProgressBase.create_progress(False, False)
    assert progress is None


def test_progress_factory_verbose() -> None:
    progress = ProgressBase.create_progress(False, True)
    assert isinstance(progress, ProgressBase)


def test_progress_factory_percent() -> None:
    progress = ProgressBase.create_progress(True, False)
    assert isinstance(progress, StandardPrintPercentOnly)


def test_simple_progress(capsys: Any) -> None:
    report = StandardPrintPercentOnly()
    src = URL("file:///abc")
    src_str = "/abc" if not sys.platform == "win32" else "\\abc"
    dst = URL("storage:xyz")
    dst_str = "storage:xyz"

    report.start(StorageProgressStart(src, dst, 600))
    captured = capsys.readouterr()
    assert captured.out == f"Start copying {src_str!r} -> {dst_str!r}.\n"

    report.step(StorageProgressStep(src, dst, 300, 600))
    captured = capsys.readouterr()
    assert captured.out == f"\r{src_str!r} -> {dst_str!r}: 50.00%."

    report.step(StorageProgressStep(src, dst, 400, 600))
    captured = capsys.readouterr()
    assert captured.out == f"\r{src_str!r} -> {dst_str!r}: 66.67%."

    report.complete(StorageProgressComplete(src, dst, 600))
    captured = capsys.readouterr()
    assert captured.out == f"\rFile {src_str!r} -> {dst_str!r} copying completed.\n"


def test_mkdir(capsys: Any) -> None:
    report = StandardPrintPercentOnly()
    src = URL("file:///abc")
    src_str = "/abc" if not sys.platform == "win32" else "\\abc"
    dst = URL("storage:xyz")
    dst_str = "storage:xyz"

    report.mkdir(StorageProgressMkdir(src, dst))
    captured = capsys.readouterr()
    assert captured.out == f"Copy directory {src_str!r} -> {dst_str!r}.\n"


def test_fail1(capsys: Any) -> None:
    report = StandardPrintPercentOnly()
    src = URL("file:///abc")
    dst = URL("storage:xyz")

    report.fail(StorageProgressFail(src, dst, "error"))
    captured = capsys.readouterr()
    assert captured.err == "Failure: '/abc' -> 'storage:xyz' [error]\n"


def test_fail2(capsys: Any) -> None:
    report = ProgressBase()
    src = URL("file:///abc")
    dst = URL("storage:xyz")

    report.fail(StorageProgressFail(src, dst, "error"))
    captured = capsys.readouterr()
    assert captured.err == "Failure: '/abc' -> 'storage:xyz' [error]\n"
