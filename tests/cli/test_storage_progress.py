import sys
from pathlib import Path
from typing import Any, Callable, Iterator, List
from unittest import mock

import click
import pytest
from yarl import URL

from neuromation.api import (
    FileStatusType,
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
    return [click.unstyle(line) for (key, is_dir, line) in report.lines]


def test_format_url_storage() -> None:
    u = URL("storage://asvetlov/folder")
    assert format_url(u) == "storage://asvetlov/folder"


def test_format_url_file() -> None:
    u = URL("file:///asvetlov/folder")
    if sys.platform == "win32":
        expected = "\\asvetlov\\folder"
    else:
        expected = "/asvetlov/folder"
    assert format_url(u) == expected


_MakeRoot = Callable[[bool, bool, bool], Root]


@pytest.fixture
def make_root() -> Iterator[_MakeRoot]:
    root = None

    def make(color: bool, tty: bool, verbose: bool) -> Root:
        nonlocal root
        root = Root(
            color,
            tty,
            (80, 25),
            True,
            60,
            Path("~/.neuro"),
            verbosity=int(verbose),
            trace=False,
            trace_hide_token=True,
            command_path="",
            command_params=[],
            skip_gmp_stats=True,
        )
        return root

    yield make
    if root is not None:
        root.close()


def test_progress_factory_none(make_root: _MakeRoot) -> None:
    progress = create_storage_progress(make_root(False, False, False), False)
    assert isinstance(progress, StreamProgress)


def test_progress_factory_verbose(make_root: _MakeRoot) -> None:
    progress = create_storage_progress(make_root(False, False, False), False)
    assert isinstance(progress, StreamProgress)


def test_progress_factory_percent(make_root: _MakeRoot) -> None:
    progress = create_storage_progress(make_root(False, False, False), True)
    assert isinstance(progress, TTYProgress)


def test_quiet_stream_progress(capsys: Any, make_root: _MakeRoot) -> None:
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


def test_stream_progress(capsys: Any, make_root: _MakeRoot) -> None:
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


def test_stream_fail1(capsys: Any, make_root: _MakeRoot) -> None:
    report = create_storage_progress(make_root(False, True, False), False)
    src = URL("file:///abc")
    src_str = "/abc" if not sys.platform == "win32" else "\\abc"
    dst = URL("storage:xyz")

    report.fail(StorageProgressFail(src, dst, "error"))
    captured = capsys.readouterr()
    assert captured.err == f"Failure: '{src_str}' -> 'storage:xyz' [error]\n"


def test_stream_fail2(capsys: Any, make_root: _MakeRoot) -> None:
    report = create_storage_progress(make_root(False, True, False), False)
    src = URL("file:///abc")
    src_str = "/abc" if not sys.platform == "win32" else "\\abc"
    dst = URL("storage:xyz")

    report.fail(StorageProgressFail(src, dst, "error"))
    captured = capsys.readouterr()
    assert captured.err == f"Failure: '{src_str}' -> 'storage:xyz' [error]\n"


def test_tty_progress(capsys: Any, make_root: _MakeRoot) -> None:
    report = create_storage_progress(make_root(False, True, False), True)
    src = URL("file:///abc")
    dst = URL("storage:xyz")
    src_f = URL("file:///abc/file.txt")
    dst_f = URL("storage:xyz/file.txt")

    report.begin(src, dst)
    captured = capsys.readouterr()
    assert captured.out == f"Copy 'file:///abc' => 'storage:xyz'\n"

    report.enter(StorageProgressEnterDir(src, dst))
    assert unstyle(report) == ["'file:///abc' ..."]

    report.start(StorageProgressStart(src_f, dst_f, 600))
    assert unstyle(report) == ["'file:///abc' ...", "'file.txt' [0.00%] 0B of 600B"]

    report.step(StorageProgressStep(src_f, dst_f, 300, 600))
    assert unstyle(report) == ["'file:///abc' ...", "'file.txt' [50.00%] 300B of 600B"]

    report.step(StorageProgressStep(src_f, dst_f, 400, 600))
    assert unstyle(report) == ["'file:///abc' ...", "'file.txt' [66.67%] 400B of 600B"]

    report.complete(StorageProgressComplete(src_f, dst_f, 600))
    assert unstyle(report) == ["'file:///abc' ...", "'file.txt' 600B"]

    report.leave(StorageProgressLeaveDir(src, dst))
    assert unstyle(report) == [
        "'file:///abc' ...",
        "'file.txt' 600B",
        "'file:///abc' DONE",
    ]


def test_tty_verbose(capsys: Any, make_root: _MakeRoot) -> None:
    report = create_storage_progress(make_root(False, True, True), True)
    src = URL("file:///abc")
    dst = URL("storage:xyz")

    report.begin(src, dst)
    captured = capsys.readouterr()
    assert captured.out == f"Copy\n'file:///abc'\n=>\n'storage:xyz'\n"


def test_tty_nested(make_root: _MakeRoot) -> None:
    report = create_storage_progress(make_root(False, True, False), True)
    src = URL("file:///abc")
    dst = URL("storage:xyz")
    src_f = URL("file:///abc/file.txt")
    dst_f = URL("storage:xyz/file.txt")
    src2 = URL("file:///abc/cde")
    dst2 = URL("storage:xyz/cde")
    src2_f = URL("file:///abc/cde/file.txt")
    dst2_f = URL("storage:xyz/cde/file.txt")

    report.enter(StorageProgressEnterDir(src, dst))
    assert unstyle(report) == ["'file:///abc' ..."]

    report.start(StorageProgressStart(src_f, dst_f, 600))
    assert unstyle(report) == ["'file:///abc' ...", "'file.txt' [0.00%] 0B of 600B"]

    report.step(StorageProgressStep(src_f, dst_f, 300, 600))
    assert unstyle(report) == ["'file:///abc' ...", "'file.txt' [50.00%] 300B of 600B"]

    report.step(StorageProgressStep(src_f, dst_f, 400, 600))
    assert unstyle(report) == ["'file:///abc' ...", "'file.txt' [66.67%] 400B of 600B"]

    report.complete(StorageProgressComplete(src_f, dst_f, 600))
    assert unstyle(report) == ["'file:///abc' ...", "'file.txt' 600B"]

    report.enter(StorageProgressEnterDir(src2, dst2))
    assert unstyle(report) == [
        "'file:///abc' ...",
        "'file.txt' 600B",
        "'file:///abc/cde' ...",
    ]

    report.start(StorageProgressStart(src2_f, dst2_f, 800))
    assert unstyle(report) == [
        "'file:///abc' ...",
        "'file.txt' 600B",
        "'file:///abc/cde' ...",
        "'file.txt' [0.00%] 0B of 800B",
    ]

    report.step(StorageProgressStep(src2_f, dst2_f, 300, 800))
    assert unstyle(report) == [
        "'file:///abc' ...",
        "'file.txt' 600B",
        "'file:///abc/cde' ...",
        "'file.txt' [37.50%] 300B of 800B",
    ]

    report.complete(StorageProgressComplete(src2_f, dst_f, 800))
    assert unstyle(report) == [
        "'file:///abc' ...",
        "'file.txt' 600B",
        "'file:///abc/cde' ...",
        "'file.txt' 800B",
    ]

    report.leave(StorageProgressLeaveDir(src2, dst2))
    assert unstyle(report) == [
        "'file:///abc' ...",
        "'file.txt' 600B",
        "'file:///abc/cde' ...",
        "'file.txt' 800B",
        "'file:///abc/cde' DONE",
    ]

    report.leave(StorageProgressLeaveDir(src, dst))
    assert unstyle(report) == [
        "'file:///abc' ...",
        "'file.txt' 600B",
        "'file:///abc/cde' ...",
        "'file.txt' 800B",
        "'file:///abc/cde' DONE",
        "'file:///abc' DONE",
    ]


def test_fail_tty(capsys: Any, make_root: _MakeRoot) -> None:
    report = create_storage_progress(make_root(False, True, False), True)
    src = URL("file:///abc")
    dst = URL("storage:xyz")

    report.fail(StorageProgressFail(src, dst, "error"))
    captured = capsys.readouterr()
    assert captured.err == f"Failure: 'file:///abc' -> 'storage:xyz' [error]\n"


def test_tty_fmt_url(make_root: _MakeRoot) -> None:
    report = create_storage_progress(make_root(False, True, False), True)
    assert isinstance(report, TTYProgress)
    url = URL("storage://andrew/folder/file.txt")
    assert (
        click.unstyle(report.fmt_url(url, FileStatusType.FILE, half=True))
        == "'storage://andrew/folder/file.txt'"
    )


def test_tty_fmt_storage_url_over_half(make_root: _MakeRoot) -> None:
    report = create_storage_progress(make_root(False, True, False), True)
    assert isinstance(report, TTYProgress)
    url = URL("storage://andrew/folder0/folder1/file.txt")
    assert (
        click.unstyle(report.fmt_url(url, FileStatusType.FILE, half=True))
        == "'storage://andrew/.../file.txt'"
    )


def test_tty_fmt_storage_url_over_full(make_root: _MakeRoot) -> None:
    report = create_storage_progress(make_root(False, True, False), True)
    assert isinstance(report, TTYProgress)
    url = URL(
        "storage://andrew/"
        + "/".join("folder" + str(i) for i in range(5))
        + "/file.txt"
    )
    assert (
        click.unstyle(report.fmt_url(url, FileStatusType.FILE, half=False))
        == "'storage://andrew/.../folder2/folder3/folder4/file.txt'"
    )


def test_tty_fmt_url_over_half_single_segment(make_root: _MakeRoot) -> None:
    report = create_storage_progress(make_root(False, True, False), True)
    assert isinstance(report, TTYProgress)
    url = URL("file://" + "a" * 40)
    assert (
        click.unstyle(report.fmt_url(url, FileStatusType.FILE, half=True))
        == "'file://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'"
    )


def test_tty_fmt_url_over_half_single_segment2(make_root: _MakeRoot) -> None:
    report = create_storage_progress(make_root(False, True, False), True)
    assert isinstance(report, TTYProgress)
    url = URL("file:///" + "a" * 40)
    assert (
        click.unstyle(report.fmt_url(url, FileStatusType.FILE, half=True))
        == "'file:///aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'"
    )


def test_tty_fmt_url_over_half_long_segment(make_root: _MakeRoot) -> None:
    report = create_storage_progress(make_root(False, True, False), True)
    assert isinstance(report, TTYProgress)
    url = URL("file:///andrew/" + "a" * 30)
    assert (
        click.unstyle(report.fmt_url(url, FileStatusType.FILE, half=True))
        == "'file:///.../aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'"
    )


def test_tty_fmt_file_url_over_half(make_root: _MakeRoot) -> None:
    report = create_storage_progress(make_root(False, True, False), True)
    assert isinstance(report, TTYProgress)
    url = URL("file:///andrew/folder0/folder1/file.txt")
    assert (
        click.unstyle(report.fmt_url(url, FileStatusType.FILE, half=True))
        == "'file:///.../folder1/file.txt'"
    )


def test_tty_fmt_file_url_over_full(make_root: _MakeRoot) -> None:
    report = create_storage_progress(make_root(False, True, False), True)
    assert isinstance(report, TTYProgress)
    url = URL(
        "file:///andrew/" + "/".join("folder" + str(i) for i in range(5)) + "/file.txt"
    )
    assert (
        click.unstyle(report.fmt_url(url, FileStatusType.FILE, half=False))
        == "'file:///.../folder0/folder1/folder2/folder3/folder4/file.txt'"
    )


def test_tty_fmt_url_relative_over(make_root: _MakeRoot) -> None:
    report = create_storage_progress(make_root(False, True, False), True)
    assert isinstance(report, TTYProgress)
    url = URL("storage:folder1/folder2/folder3/folder4/folder5")
    assert (
        click.unstyle(report.fmt_url(url, FileStatusType.FILE, half=True))
        == "'storage:.../folder3/folder4/folder5'"
    )


def test_tty_fmt_url_relative_over_long_2_segments(make_root: _MakeRoot) -> None:
    report = create_storage_progress(make_root(False, True, False), True)
    assert isinstance(report, TTYProgress)
    url = URL("storage:folder/" + "a" * 30)
    assert (
        click.unstyle(report.fmt_url(url, FileStatusType.FILE, half=True))
        == "'storage:.../aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'"
    )


def test_tty_fmt_url_relative_over_single_segment(make_root: _MakeRoot) -> None:
    report = create_storage_progress(make_root(False, True, False), True)
    assert isinstance(report, TTYProgress)
    url = URL("storage:" + "a" * 35)
    assert (
        click.unstyle(report.fmt_url(url, FileStatusType.FILE, half=True))
        == "'storage:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'"
    )


def test_tty_append_files(make_root: _MakeRoot) -> None:
    with mock.patch.object(TTYProgress, "HEIGHT", 3):
        report = create_storage_progress(make_root(False, True, False), True)
        assert isinstance(report, TTYProgress)
        mock.patch.object(report, "HEIGHT", 3)
        assert report.lines == []
        report.append(URL("a"), "a")
        assert report.lines == [(URL("a"), False, "a")]
        report.append(URL("b"), "b")
        assert report.lines == [(URL("a"), False, "a"), (URL("b"), False, "b")]
        report.append(URL("c"), "c")
        assert report.lines == [
            (URL("a"), False, "a"),
            (URL("b"), False, "b"),
            (URL("c"), False, "c"),
        ]
        report.append(URL("d"), "d")
        assert report.lines == [
            (URL("b"), False, "b"),
            (URL("c"), False, "c"),
            (URL("d"), False, "d"),
        ]


def test_tty_append_dir(make_root: _MakeRoot) -> None:
    with mock.patch.object(TTYProgress, "HEIGHT", 3):
        report = create_storage_progress(make_root(False, True, False), True)
        assert isinstance(report, TTYProgress)
        mock.patch.object(report, "HEIGHT", 3)
        assert report.lines == []
        report.append(URL("a"), "a", is_dir=True)
        assert report.lines == [(URL("a"), True, "a")]
        report.append(URL("a/b"), "b")
        assert report.lines == [(URL("a"), True, "a"), (URL("a/b"), False, "b")]
        report.append(URL("a/c"), "c")
        assert report.lines == [
            (URL("a"), True, "a"),
            (URL("a/b"), False, "b"),
            (URL("a/c"), False, "c"),
        ]
        report.append(URL("a/d"), "d")
        assert report.lines == [
            (URL("a"), True, "a"),
            (URL("a/c"), False, "c"),
            (URL("a/d"), False, "d"),
        ]


def test_tty_append_second_dir(make_root: _MakeRoot) -> None:
    with mock.patch.object(TTYProgress, "HEIGHT", 3):
        report = create_storage_progress(make_root(False, True, False), True)
        assert isinstance(report, TTYProgress)
        mock.patch.object(report, "HEIGHT", 3)
        assert report.lines == []
        report.append(URL("a"), "a", is_dir=True)
        assert report.lines == [(URL("a"), True, "a")]
        report.append(URL("b"), "b")
        assert report.lines == [(URL("a"), True, "a"), (URL("b"), False, "b")]
        report.append(URL("c"), "c", is_dir=True)
        assert report.lines == [
            (URL("a"), True, "a"),
            (URL("b"), False, "b"),
            (URL("c"), True, "c"),
        ]
        report.append(URL("d"), "d")
        assert report.lines == [
            (URL("a"), True, "a"),
            (URL("c"), True, "c"),
            (URL("d"), False, "d"),
        ]
