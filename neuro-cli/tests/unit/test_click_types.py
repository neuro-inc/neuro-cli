from pathlib import Path
from typing import Tuple

import click
import pytest

from neuro_cli.click_types import (
    JOB_NAME,
    LocalRemotePortParamType,
    StoragePathType,
    _merge_autocompletion_args,
)
from neuro_cli.root import Root


@pytest.mark.parametrize(
    "arg,val",
    [("1:1", (1, 1)), ("1:10", (1, 10)), ("434:1", (434, 1)), ("0897:123", (897, 123))],
)
def test_local_remote_port_param_type_valid(arg: str, val: Tuple[int, int]) -> None:
    param = LocalRemotePortParamType()
    assert param.convert(arg, None, None) == val


@pytest.mark.parametrize(
    "arg",
    [
        "1:",
        "-123:10",
        "34:-65500",
        "hello:45",
        "5555:world",
        "65536:1",
        "0:0",
        "none",
        "",
    ],
)
def test_local_remote_port_param_type_invalid(arg: str) -> None:
    param = LocalRemotePortParamType()
    with pytest.raises(click.BadParameter, match=".* is not a valid port combination"):
        param.convert(arg, None, None)


class TestJobNameType:
    def test_ok(self) -> None:
        name = "a-bc-def"
        assert name == JOB_NAME.convert(name, param=None, ctx=None)

    def test_too_short(self) -> None:
        with pytest.raises(ValueError, match="Invalid job name"):
            JOB_NAME.convert("a" * 2, param=None, ctx=None)

    def test_too_long(self) -> None:
        with pytest.raises(ValueError, match="Invalid job name"):
            JOB_NAME.convert("a" * 41, param=None, ctx=None)

    @pytest.mark.parametrize(
        "name",
        [
            "abc@",  # invalid character
            "abc-DEF",  # capital letters
            "abc--def",  # two consequent hyphens
            "-abc-def",  # hyphen as the first symbol
            "abc-def-",  # hyphen as the last symbol
        ],
    )
    def test_invalid_pattern(self, name: str) -> None:
        with pytest.raises(ValueError, match="Invalid job name"):
            JOB_NAME.convert(name, param=None, ctx=None)


class TestStoragePathType:
    async def test_find_matches_scheme(self, root: Root) -> None:
        spt = StoragePathType()
        ret = await spt._find_matches("st", root)
        assert len(ret) == 1
        assert "storage:" == ret[0].value

    async def test_find_matches_invalid_scheme(self, root: Root) -> None:
        spt = StoragePathType()
        ret = await spt._find_matches("unknown", root)
        assert ret == []

    async def test_find_matches_file(self, root: Root) -> None:
        spt = StoragePathType()
        fobj = Path(__file__)
        ret = await spt._find_matches(fobj.as_uri(), root)
        assert [i.value for i in ret] == [fobj.name]
        assert {i.type for i in ret} == {"uri"}
        assert {i.prefix for i in ret} == {fobj.parent.as_uri() + "/"}

    async def test_find_matches_files_only(self, root: Root) -> None:
        spt = StoragePathType(complete_dir=False)
        fobj = Path(__file__).parent
        incomplete = fobj.as_uri()
        ret = await spt._find_matches(incomplete, root)
        assert [i.value for i in ret] == [
            f.name for f in fobj.iterdir() if not f.is_dir()
        ]
        assert {i.type for i in ret} == {"uri"}
        assert {i.prefix for i in ret} == {fobj.as_uri() + "/"}

    async def test_find_matches_dir(self, root: Root) -> None:
        spt = StoragePathType()
        fobj = Path(__file__).parent
        ret = await spt._find_matches(fobj.as_uri(), root)
        assert [i.value for i in ret] == [
            f.name + "/" if f.is_dir() else f.name for f in fobj.iterdir()
        ]
        assert {i.type for i in ret} == {"uri"}
        assert {i.prefix for i in ret} == {fobj.as_uri() + "/"}

    async def test_find_matches_dir_only(self, root: Root) -> None:
        spt = StoragePathType(complete_file=False)
        fobj = Path(__file__).parent
        ret = await spt._find_matches(fobj.as_uri(), root)
        assert [i.value for i in ret] == [
            f.name + "/" for f in fobj.iterdir() if f.is_dir()
        ]
        assert {i.type for i in ret} == {"uri"}
        assert {i.prefix for i in ret} == {fobj.as_uri() + "/"}

    async def test_find_matches_partial(self, root: Root) -> None:
        spt = StoragePathType()
        fobj = Path(__file__).parent
        incomplete = fobj.as_uri() + "/test_"
        ret = await spt._find_matches(incomplete, root)
        assert [i.value for i in ret] == [
            f.name + "/" if f.is_dir() else f.name for f in fobj.glob("test_*")
        ]
        assert {i.type for i in ret} == {"uri"}
        assert {i.prefix for i in ret} == {fobj.as_uri() + "/"}

    async def test_find_matches_not_exists(self, root: Root) -> None:
        spt = StoragePathType()
        fobj = Path(__file__).parent
        incomplete = fobj.as_uri() + "/file-not-found.txt"
        ret = await spt._find_matches(incomplete, root)
        assert [] == ret


def test_merge_autocompletion_args() -> None:
    assert _merge_autocompletion_args(["ls"], "st") == (["ls"], "st")
    assert _merge_autocompletion_args(["ls", "storage"], ":") == (["ls"], "storage:")
    assert _merge_autocompletion_args(["ls", "storage", ":"], "dir") == (
        [
            "ls",
        ],
        "storage:dir",
    )
