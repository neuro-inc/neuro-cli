from typing import Tuple

import click
import pytest

from neuromation.cli.click_types import JOB_NAME, LocalRemotePortParamType


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
