import sys
from pathlib import Path
from typing import Any, List

import click
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
from neuromation.cli.formatters.storage import (
    BaseStorageProgress,
    StreamProgress,
    TTYProgress,
    format_url,
)
from neuromation.cli.root import Root


def unstyle(report: BaseStorageProgress) -> List[str]:
    assert isinstance(report, TTYProgress)
    return [click.unstyle(line) for (is_dir, line) in report.lines]


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
    src_f = URL("file:///abc/file.txt")
    dst_f = URL("storage:xyz/file.txt")

    report.begin(src, dst)
    captured = capsys.readouterr()
    assert captured.out == f"Copy file:///abc => storage:xyz\n"

    report.enter(StorageProgressEnterDir(src, dst))
    assert unstyle(report) == ["file:///abc"]

    report.start(StorageProgressStart(src_f, dst_f, 600))
    assert unstyle(report) == ["file:///abc", "file.txt [0.00%] 0B of 600B"]

    report.step(StorageProgressStep(src_f, dst_f, 300, 600))
    assert unstyle(report) == ["file:///abc", "file.txt [50.00%] 300B of 600B"]

    report.step(StorageProgressStep(src_f, dst_f, 400, 600))
    assert unstyle(report) == ["file:///abc", "file.txt [66.67%] 400B of 600B"]

    report.complete(StorageProgressComplete(src_f, dst_f, 600))
    assert unstyle(report) == ["file:///abc", "file.txt 600B"]

    report.leave(StorageProgressLeaveDir(src, dst))
    assert unstyle(report) == ["file:///abc", "file.txt 600B"]


def test_tty_verbose(capsys: Any) -> None:
    report = create_storage_progress(make_root(True, True, True), True)
    src = URL("file:///abc")
    dst = URL("storage:xyz")

    report.begin(src, dst)
    captured = capsys.readouterr()
    assert captured.out == f"Copy\nfile:///abc\n=>\nstorage:xyz\n"


def test_tty_nested() -> None:
    report = create_storage_progress(make_root(True, True, False), True)
    src = URL("file:///abc")
    dst = URL("storage:xyz")
    src_f = URL("file:///abc/file.txt")
    dst_f = URL("storage:xyz/file.txt")
    src2 = URL("file:///abc/cde")
    dst2 = URL("storage:xyz/cde")
    src2_f = URL("file:///abc/cde/file.txt")
    dst2_f = URL("storage:xyz/cde/file.txt")

    report.enter(StorageProgressEnterDir(src, dst))
    assert unstyle(report) == ["file:///abc"]

    report.start(StorageProgressStart(src_f, dst_f, 600))
    assert unstyle(report) == ["file:///abc", "file.txt [0.00%] 0B of 600B"]

    report.step(StorageProgressStep(src_f, dst_f, 300, 600))
    assert unstyle(report) == ["file:///abc", "file.txt [50.00%] 300B of 600B"]

    report.step(StorageProgressStep(src_f, dst_f, 400, 600))
    assert unstyle(report) == ["file:///abc", "file.txt [66.67%] 400B of 600B"]

    report.complete(StorageProgressComplete(src_f, dst_f, 600))
    assert unstyle(report) == ["file:///abc", "file.txt 600B"]

    report.enter(StorageProgressEnterDir(src2, dst2))
    assert unstyle(report) == ["file:///abc", "file.txt 600B", "file:///abc/cde"]

    report.start(StorageProgressStart(src2_f, dst2_f, 800))
    assert unstyle(report) == [
        "file:///abc",
        "file.txt 600B",
        "file:///abc/cde",
        "file.txt [0.00%] 0B of 800B",
    ]

    report.step(StorageProgressStep(src2_f, dst2_f, 300, 800))
    assert unstyle(report) == [
        "file:///abc",
        "file.txt 600B",
        "file:///abc/cde",
        "file.txt [37.50%] 300B of 800B",
    ]

    report.complete(StorageProgressComplete(src2_f, dst_f, 800))
    assert unstyle(report) == [
        "file:///abc",
        "file.txt 600B",
        "file:///abc/cde",
        "file.txt 800B",
    ]

    report.leave(StorageProgressLeaveDir(src2, dst2))
    assert unstyle(report) == [
        "file:///abc",
        "file.txt 600B",
        "file:///abc/cde",
        "file.txt 800B",
        "file:///abc",
    ]

    report.leave(StorageProgressLeaveDir(src, dst))
    assert unstyle(report) == [
        "file:///abc",
        "file.txt 600B",
        "file:///abc/cde",
        "file.txt 800B",
        "file:///abc",
    ]


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


def test_fail_tty(capsys: Any) -> None:
    report = create_storage_progress(make_root(False, True, False), True)
    src = URL("file:///abc")
    dst = URL("storage:xyz")

    report.fail(StorageProgressFail(src, dst, "error"))
    captured = capsys.readouterr()
    assert captured.err == f"Failure: 'file:///abc' -> 'storage:xyz' [error]\n"
