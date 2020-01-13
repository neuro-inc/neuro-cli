import os.path

from neuromation.api.file_filter import FileFilter


def test_empty_filter() -> None:
    ff = FileFilter()
    assert ff.match("spam")
    assert ff.match(".spam")
    assert ff.match("spam/ham")
    assert ff.match(os.path.join("spam", "ham"))


def test_exclude_all() -> None:
    ff = FileFilter()
    ff.exclude("*")
    assert not ff.match("spam")
    assert not ff.match(".spam")


def test_exclude() -> None:
    ff = FileFilter()
    ff.exclude("*.txt")
    assert ff.match("spam")
    assert not ff.match("spam.txt")


def test_exclude_include() -> None:
    ff = FileFilter()
    ff.exclude("*.txt")
    ff.include("s*")
    assert ff.match("spam")
    assert ff.match("spam.txt")
    assert ff.match("ham")
    assert not ff.match("ham.txt")
