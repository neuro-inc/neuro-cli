import os.path

from neuromation.api.file_filter import FileFilter


async def test_empty_filter() -> None:
    ff = FileFilter()
    assert await ff.match("spam")
    assert await ff.match(".spam")
    assert await ff.match("spam/ham")
    assert await ff.match(os.path.join("spam", "ham"))


async def test_exclude_all() -> None:
    ff = FileFilter()
    ff.exclude("*")
    assert not await ff.match("spam")
    assert not await ff.match(".spam")


async def test_exclude() -> None:
    ff = FileFilter()
    ff.exclude("*.txt")
    assert await ff.match("spam")
    assert not await ff.match("spam.txt")


async def test_exclude_include() -> None:
    ff = FileFilter()
    ff.exclude("*.txt")
    ff.include("s*")
    assert await ff.match("spam")
    assert await ff.match("spam.txt")
    assert await ff.match("ham")
    assert not await ff.match("ham.txt")
