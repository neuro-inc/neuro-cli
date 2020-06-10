from neuromation.api.file_filter import FileFilter, translate


async def test_empty_filter() -> None:
    ff = FileFilter()
    assert await ff.match("spam")
    assert await ff.match(".spam")
    assert await ff.match("spam/ham")


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
    assert not await ff.match("dir/spam.txt")
    assert await ff.match("dir.txt/spam")
    assert await ff.match("dir/child.txt/spam")


async def test_exclude_include() -> None:
    ff = FileFilter()
    ff.exclude("*.txt")
    ff.include("s*")
    assert await ff.match("spam")
    assert await ff.match("spam.txt")
    assert await ff.match("ham")
    assert not await ff.match("ham.txt")
    assert await ff.match("dir/spam.txt")
    assert not await ff.match("dir/ham.txt")
    assert await ff.match("dir.txt/spam")


async def test_exclude_with_slash() -> None:
    ff = FileFilter()
    ff.exclude("dir/*.txt")
    assert await ff.match("spam.txt")
    assert not await ff.match("dir/spam.txt")
    assert await ff.match("parent/dir/spam.txt")


async def test_exclude_crosscomponent() -> None:
    ff = FileFilter()
    ff.exclude("a?b")
    assert not await ff.match("a-b")
    assert await ff.match("a/b")

    ff = FileFilter()
    ff.exclude("a*b")
    assert not await ff.match("ab")
    assert not await ff.match("a-b")
    assert not await ff.match("arab")
    assert await ff.match("a/b")
    assert await ff.match("alice/bob")

    ff = FileFilter()
    ff.exclude("a[!0-9]b")
    assert await ff.match("a0b")
    assert not await ff.match("a-b")
    assert await ff.match("a/b")


async def test_exclude_recursive() -> None:
    ff = FileFilter()
    ff.exclude("**/dir/*.txt")
    assert await ff.match("spam.txt")
    assert not await ff.match("dir/spam.txt")
    assert await ff.match("dir/spam")
    assert not await ff.match("parent/dir/spam.txt")
    assert await ff.match("parent/dir/spam")

    ff = FileFilter()
    ff.exclude("dir/**/*.txt")
    assert await ff.match("spam.txt")
    assert not await ff.match("dir/spam.txt")
    assert await ff.match("dir/spam")
    assert not await ff.match("dir/child/spam.txt")
    assert await ff.match("dir/child/spam")

    ff = FileFilter()
    ff.exclude("dir/**")
    assert await ff.match("spam")
    assert not await ff.match("dir/")
    assert await ff.match("dir")
    assert not await ff.match("dir/child")
    assert not await ff.match("dir/child/spam")

    ff = FileFilter()
    ff.exclude("dir/**/")
    assert await ff.match("spam")
    assert not await ff.match("dir/")
    assert await ff.match("dir")
    assert not await ff.match("dir/child/")
    assert await ff.match("dir/child")
    assert not await ff.match("dir/child/spam/")
    assert await ff.match("dir/child/spam")


def test_translate() -> None:
    assert translate("") == ""
    assert translate("abc") == "abc"
    assert translate("a?c") == "a[^/]c"
    assert translate("a*c") == "a[^/]*c"
    assert translate("a[bc]d") == "a[bc](?<!/)d"
    assert translate("a[b-d]e") == "a[b-d](?<!/)e"
    assert translate("a[!b-d]e") == "a[^b-d](?<!/)e"
    assert translate("[a-zA-Z_]") == "[a-zA-Z_](?<!/)"


def test_translate_recursive() -> None:
    assert translate("**") == ".*"
    assert translate("**/") == f"(?:.+/)?"
    assert translate("**/abc") == f"(?:.+/)?abc"
    assert translate("/**") == f"/.*"
    assert translate("abc/**") == f"abc/.*"
    assert translate("/**/") == f"/(?:.+/)?"
    assert translate("abc/**/def") == f"abc/(?:.+/)?def"
