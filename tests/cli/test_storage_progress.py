import sys
from pathlib import Path
from typing import Any

from yarl import URL

from neuromation.api import (
    StorageProgressComplete,
    StorageProgressEnterDir,
    StorageProgressFail,
    StorageProgressLeaveDir,
    StorageProgressStart,
    StorageProgressStep,
)
from neuromation.cli.formatters import create_storage_progress
from neuromation.cli.formatters.storage import StreamProgress, TTYProgress, format_url
from neuromation.cli.root import Root


def test_format_url_storage() -> None:
    u = URL("storage://asvetlov/folder")
    assert format_url(u) == "storage://asvetlov/folder"


def test_format_url_file() -> None:
    u = URL("file:///asvetlov/folder")
    assert format_url(u) == "/asvetlov/folder"


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


def test_quiet_stream_progress(capsys: Any) -> None:
    report = create_storage_progress(make_root(False, False, False), False)
    src = URL("file:///abc")
    dst = URL("storage:xyz")

    report.begin(src, dst)
    captured = capsys.readouterr()
    assert captured.out == f""

    report.enter(StorageProgressEnterDir(src, dst))
    captured = capsys.readouterr()
    assert captured.out == f""

    report.start(StorageProgressStart(src, dst, 600))
    captured = capsys.readouterr()
    assert captured.out == f""

    report.step(StorageProgressStep(src, dst, 300, 600))
    captured = capsys.readouterr()
    assert captured.out == ""

    report.step(StorageProgressStep(src, dst, 400, 600))
    captured = capsys.readouterr()
    assert captured.out == ""

    report.complete(StorageProgressComplete(src, dst, 600))
    captured = capsys.readouterr()
    assert captured.out == f""

    report.leave(StorageProgressLeaveDir(src, dst))
    captured = capsys.readouterr()
    assert captured.out == f""


def test_stream_progress(capsys: Any) -> None:
    report = create_storage_progress(make_root(False, False, True), False)
    src = URL("file:///abc")
    src_str = "/abc" if not sys.platform == "win32" else "\\abc"
    dst = URL("storage:xyz")
    dst_str = "storage:xyz"

    report.begin(src, dst)
    captured = capsys.readouterr()
    assert captured.out == f"Copy '{src_str}' -> '{dst_str}'\n"

    report.enter(StorageProgressEnterDir(src, dst))
    captured = capsys.readouterr()
    assert captured.out == f"'{src_str}' -> '{dst_str}'\n"

    report.start(StorageProgressStart(src, dst, 600))
    captured = capsys.readouterr()
    assert captured.out == f""

    report.step(StorageProgressStep(src, dst, 300, 600))
    captured = capsys.readouterr()
    assert captured.out == ""

    report.step(StorageProgressStep(src, dst, 400, 600))
    captured = capsys.readouterr()
    assert captured.out == ""

    report.complete(StorageProgressComplete(src, dst, 600))
    captured = capsys.readouterr()
    assert captured.out == f"'{src_str}' -> '{dst_str}'\n"

    report.leave(StorageProgressLeaveDir(src, dst))
    captured = capsys.readouterr()
    assert captured.out == f""


def test_tty_progress(capsys: Any) -> None:
    report = create_storage_progress(make_root(True, True, False), True)
    src = URL("file:///abc")
    dst = URL("storage:xyz")

    report.begin(src, dst)
    captured = capsys.readouterr()
    assert captured.out == f"Copy file:///abc => storage:xyz\n"

    report.enter(StorageProgressEnterDir(src, dst))
    captured = capsys.readouterr()
    assert captured.out == f"file:///abc\n"

    report.start(StorageProgressStart(src, dst, 600))
    captured = capsys.readouterr()
    assert captured.out == f"file:///abc\nabc [0.00%] 0B of 600B\n"

    report.step(StorageProgressStep(src, dst, 300, 600))
    captured = capsys.readouterr()
    assert captured.out == "abc [50.00%] 300B of 600B\n"

    report.step(StorageProgressStep(src, dst, 400, 600))
    captured = capsys.readouterr()
    assert captured.out == "abc [66.67%] 400B of 600B\n"

    report.complete(StorageProgressComplete(src, dst, 600))
    captured = capsys.readouterr()
    assert captured.out == f"abc 600B\n"

    report.leave(StorageProgressLeaveDir(src, dst))
    captured = capsys.readouterr()
    assert captured.out == f""


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
