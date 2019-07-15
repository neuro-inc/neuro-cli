from typing import Any

from yarl import URL

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
    dst = URL("storage:xyz")

    report.start(src, dst, 600)
    captured = capsys.readouterr()
    assert captured.out == f"Start copying {src!r} -> {dst!r}.\n"

    report.progress(src, dst, 300)
    captured = capsys.readouterr()
    assert captured.out == f"\r{src!r} -> {dst!r}: 50.00%."

    report.progress(src, dst, 400)
    captured = capsys.readouterr()
    assert captured.out == f"\r{src!r} -> {dst!r}: 66.67%."

    report.complete(src, dst)
    captured = capsys.readouterr()
    assert captured.out == f"\rFile {src!r} -> {dst!r} copying completed.\n"


def test_mkdir(capsys: Any) -> None:
    report = StandardPrintPercentOnly()
    src = URL("file:///abc")
    dst = URL("storage:xyz")

    report.mkdir(src, dst)
    captured = capsys.readouterr()
    assert captured.out == f"Copy directory {src!r} -> {dst!r}.\n"
