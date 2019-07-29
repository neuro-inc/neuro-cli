import sys
from pathlib import Path
from typing import Any

from yarl import URL

from neuromation.api import (
    StorageProgressComplete,
    StorageProgressEnterDir,
    StorageProgressFail,
    StorageProgressStep,
)
from neuromation.cli.formatters import create_storage_progress
from neuromation.cli.formatters.storage import StreamProgress, TTYProgress
from neuromation.cli.root import Root


def make_root(color: bool, tty: bool, verbose: bool) -> Root:
    return Root(color, tty, (80, 25), True, 60, Path("~/.nmrc"), verbosity=int(verbose))


def test_progress_factory_none() -> None:
    progress = create_storage_progress(make_root(False, False, False), False)
    assert isinstance(progress, StreamProgress)


def test_progress_factory_verbose() -> None:
    progress = create_storage_progress(make_root(False, False, False), False)
    assert isinstance(progress, StreamProgress)


def test_progress_factory_percent() -> None:
    progress = create_storage_progress(make_root(False, False, False), True)
    assert isinstance(progress, TTYProgress)


def test_simple_progress(capsys: Any) -> None:
    report = create_storage_progress(make_root(False, False, True), False)
    src = URL("file:///abc")
    src_str = "/abc" if not sys.platform == "win32" else "\\abc"
    dst = URL("storage:xyz")
    dst_str = "storage:xyz"

    report.enter(StorageProgressEnterDir(src, dst))
    captured = capsys.readouterr()
    assert captured.out == f"'{src_str}' -> '{dst_str}'\n"

    report.step(StorageProgressStep(src, dst, 300, 600))
    captured = capsys.readouterr()
    assert captured.out == ""

    report.step(StorageProgressStep(src, dst, 400, 600))
    captured = capsys.readouterr()
    assert captured.out == ""

    report.complete(StorageProgressComplete(src, dst, 600))
    captured = capsys.readouterr()
    assert captured.out == f"'{src_str}' -> '{dst_str}'\n"


def test_fail1(capsys: Any) -> None:
    report = create_storage_progress(make_root(False, True, False), False)
    src = URL("file:///abc")
    src_str = "/abc" if not sys.platform == "win32" else "\\abc"
    dst = URL("storage:xyz")

    report.fail(StorageProgressFail(src, dst, "error"))
    captured = capsys.readouterr()
    assert captured.err == f"Failure: '{src_str}' -> 'storage:xyz' [error]\n"


def test_fail2(capsys: Any) -> None:
    report = create_storage_progress(make_root(False, True, False), False)
    src = URL("file:///abc")
    src_str = "/abc" if not sys.platform == "win32" else "\\abc"
    dst = URL("storage:xyz")

    report.fail(StorageProgressFail(src, dst, "error"))
    captured = capsys.readouterr()
    assert captured.err == f"Failure: '{src_str}' -> 'storage:xyz' [error]\n"
