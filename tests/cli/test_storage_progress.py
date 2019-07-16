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
from neuromation.cli.formatters import create_storage_progress
from neuromation.cli.formatters.storage import (
    NoPercentPrinter,
    QuietPrinter,
    StandardPrintPercentOnly,
)


def test_progress_factory_none() -> None:
    progress = create_storage_progress(False, False, False)
    assert isinstance(progress, QuietPrinter)


def test_progress_factory_verbose() -> None:
    progress = create_storage_progress(False, False, True)
    assert isinstance(progress, NoPercentPrinter)


def test_progress_factory_percent() -> None:
    progress = create_storage_progress(False, True, False)
    assert isinstance(progress, StandardPrintPercentOnly)


def test_simple_progress(capsys: Any) -> None:
    report = create_storage_progress(False, True, False)
    src = URL("file:///abc")
    src_str = "/abc" if not sys.platform == "win32" else "\\abc"
    dst = URL("storage:xyz")
    dst_str = "storage:xyz"

    report.start(StorageProgressStart(src, dst, 600))
    captured = capsys.readouterr()
    assert captured.out == f"Start copying '{src_str}' -> '{dst_str}'.\n"

    report.step(StorageProgressStep(src, dst, 300, 600))
    captured = capsys.readouterr()
    assert captured.out == f"\r'{src_str}' -> '{dst_str}': 50.00%."

    report.step(StorageProgressStep(src, dst, 400, 600))
    captured = capsys.readouterr()
    assert captured.out == f"\r'{src_str}' -> '{dst_str}': 66.67%."

    report.complete(StorageProgressComplete(src, dst, 600))
    captured = capsys.readouterr()
    assert captured.out == f"\rFile '{src_str}' -> '{dst_str}' copying completed.\n"


def test_mkdir(capsys: Any) -> None:
    report = create_storage_progress(False, True, False)
    src = URL("file:///abc")
    src_str = "/abc" if not sys.platform == "win32" else "\\abc"
    dst = URL("storage:xyz")
    dst_str = "storage:xyz"

    report.mkdir(StorageProgressMkdir(src, dst))
    captured = capsys.readouterr()
    assert captured.out == f"Copy directory '{src_str}' -> '{dst_str}'.\n"


def test_fail1(capsys: Any) -> None:
    report = create_storage_progress(False, True, False)
    src = URL("file:///abc")
    src_str = "/abc" if not sys.platform == "win32" else "\\abc"
    dst = URL("storage:xyz")

    report.fail(StorageProgressFail(src, dst, "error"))
    captured = capsys.readouterr()
    assert captured.err == f"Failure: '{src_str}' -> 'storage:xyz' [error]\n"


def test_fail2(capsys: Any) -> None:
    report = create_storage_progress(False, False, True)
    src = URL("file:///abc")
    src_str = "/abc" if not sys.platform == "win32" else "\\abc"
    dst = URL("storage:xyz")

    report.fail(StorageProgressFail(src, dst, "error"))
    captured = capsys.readouterr()
    assert captured.err == f"Failure: '{src_str}' -> 'storage:xyz' [error]\n"
