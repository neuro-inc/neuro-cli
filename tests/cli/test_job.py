import logging
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable, Tuple

import click
import pytest
import toml

from neuromation.api import Client, JobStatus
from neuromation.cli.job import (
    DEFAULT_JOB_LIFE_SPAN,
    NEUROMATION_ROOT_ENV_VAR,
    _parse_cmd,
    _parse_timedelta,
    build_env,
    calc_columns,
    calc_life_span,
    calc_statuses,
)
from neuromation.cli.parse_utils import COLUMNS_MAP, get_default_columns


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_MakeClient = Callable[..., Client]


@pytest.mark.parametrize("statuses", [("all",), ("all", "failed", "succeeded")])
def test_calc_statuses__contains_all__all_statuses_true(statuses: Tuple[str]) -> None:
    with pytest.raises(
        click.UsageError,
        match="Parameters `-a/--all` and " "`-s all/--status=all` are incompatible$",
    ):
        calc_statuses(statuses, all=True)


@pytest.mark.parametrize("statuses", [("all",), ("all", "failed", "succeeded")])
def test_calc_statuses__contains_all__all_statuses_false(
    capsys: Any, caplog: Any, statuses: Tuple[str]
) -> None:
    calc_statuses(statuses, all=False)
    std = capsys.readouterr()
    assert not std.out
    assert std.err == (
        "DeprecationWarning: "
        "Option `-s all/--status=all` is deprecated. "
        "Please use `-a/--all` instead.\n"
    )
    assert not caplog.text


def test_calc_statuses__not_contains_all__all_statuses_true(
    capsys: Any, caplog: Any
) -> None:
    assert calc_statuses(["succeeded", "pending"], all=True) == set()
    std = capsys.readouterr()
    assert not std.out
    assert not std.err
    warning = (
        "Option `-a/--all` overwrites option(s) "
        "`--status=succeeded --status=pending`"
    )
    assert warning in caplog.text


def test_calc_statuses__not_contains_all__all_statuses_true__quiet_mode(
    capsys: Any, caplog: Any
) -> None:
    root_logger = logging.getLogger()
    handler = root_logger.handlers[-1]
    assert handler.formatter
    handler.setLevel(logging.ERROR)

    assert calc_statuses(["succeeded", "pending"], all=True) == set()
    std = capsys.readouterr()
    assert not std.out
    assert not std.err
    assert not caplog.text


def test_calc_statuses__not_contains_all__all_statuses_false(
    capsys: Any, caplog: Any
) -> None:
    assert calc_statuses(["succeeded", "pending"], all=False) == {
        JobStatus.SUCCEEDED,
        JobStatus.PENDING,
    }
    std = capsys.readouterr()
    assert not std.out
    assert not std.err
    assert not caplog.text


def test_calc_statuses__check_defaults__all_statuses_false(
    capsys: Any, caplog: Any
) -> None:
    assert calc_statuses([], all=False) == {JobStatus.PENDING, JobStatus.RUNNING}
    std = capsys.readouterr()
    assert not std.out
    assert not std.err
    assert not caplog.text


def test_calc_statuses__check_defaults__all_statuses_true(
    capsys: Any, caplog: Any
) -> None:
    assert calc_statuses([], all=True) == set()
    std = capsys.readouterr()
    assert not std.out
    assert not std.err
    assert not caplog.text


@pytest.mark.parametrize(
    "env_var", [NEUROMATION_ROOT_ENV_VAR, f"{NEUROMATION_ROOT_ENV_VAR}=value"]
)
def test_build_env_reserved_env_var_conflict_passed_as_parameter(env_var: str) -> None:
    env = ("ENV_VAR_1=value", "ENV_VAR_2=value", env_var)
    with pytest.raises(
        click.UsageError,
        match="Unable to re-define system-reserved environment variable",
    ):
        build_env(env, env_file=None)


@pytest.mark.parametrize(
    "env_var", [NEUROMATION_ROOT_ENV_VAR, f"{NEUROMATION_ROOT_ENV_VAR}=value"]
)
def test_build_env_reserved_env_var_conflict_passed_in_file(
    env_var: str, tmp_path: Path
) -> None:
    env_1 = ("ENV_VAR_1=value",)
    env_2 = ("ENV_VAR_2=value", env_var)
    env_file = tmp_path / "env_var.txt"
    env_file.write_text("\n".join(env_2))

    with pytest.raises(
        click.UsageError,
        match="Unable to re-define system-reserved environment variable",
    ):
        build_env(env_1, env_file=str(env_file))


def test_build_env_blank_lines(tmp_path: Path) -> None:
    env_file = tmp_path / "env_var.txt"
    env_file.write_text("ENV_VAR_1=value1\n\n  \n\t\nENV_VAR_2=value2")
    assert build_env([], env_file=str(env_file)) == {
        "ENV_VAR_1": "value1",
        "ENV_VAR_2": "value2",
    }


def test_build_env_comments(tmp_path: Path) -> None:
    env_file = tmp_path / "env_var.txt"
    env_file.write_text("ENV_VAR_1=value1\n#ENV_VAR_2=value2\nENV_VAR_3=#value3#")
    assert build_env([], env_file=str(env_file)) == {
        "ENV_VAR_1": "value1",
        "ENV_VAR_3": "#value3#",
    }


async def test_calc_columns_section_doesnt_exist(
    monkeypatch: Any, tmp_path: Path, make_client: _MakeClient
) -> None:

    async with make_client("https://example.com") as client:
        monkeypatch.chdir(tmp_path)
        local_conf = tmp_path / ".neuro.toml"
        # empty config
        local_conf.write_text("")
        assert await calc_columns(client, None) == get_default_columns()


async def test_calc_columns_user_spec(
    monkeypatch: Any, tmp_path: Path, make_client: _MakeClient
) -> None:

    async with make_client("https://example.com") as client:
        monkeypatch.chdir(tmp_path)
        local_conf = tmp_path / ".neuro.toml"
        # empty config
        local_conf.write_text(toml.dumps({"job": {"ps-format": "{id}, {status}"}}))
        assert await calc_columns(client, None) == [
            COLUMNS_MAP["id"],
            COLUMNS_MAP["status"],
        ]


async def test_calc_life_span_none_default(
    monkeypatch: Any, tmp_path: Path, make_client: _MakeClient
) -> None:
    async with make_client("https://example.com") as client:
        monkeypatch.chdir(tmp_path)
        local_conf = tmp_path / ".neuro.toml"
        local_conf.write_text(toml.dumps({"job": {"life-span": "1d2h3m4s"}}))
        expected = timedelta(days=1, hours=2, minutes=3, seconds=4)
        assert await calc_life_span(client, None) == expected.total_seconds()


async def test_calc_life_span_zero(make_client: _MakeClient) -> None:
    async with make_client("https://example.com") as client:
        assert await calc_life_span(client, "0") is None


async def test_calc_life_span_default_life_span_all_keys(
    caplog: Any, monkeypatch: Any, tmp_path: Path, make_client: _MakeClient
) -> None:
    async with make_client("https://example.com") as client:
        monkeypatch.chdir(tmp_path)
        local_conf = tmp_path / ".neuro.toml"
        # empty config
        local_conf.write_text(toml.dumps({"job": {"life-span": "1d2h3m4s"}}))

        expected = timedelta(days=1, hours=2, minutes=3, seconds=4)
        assert await calc_life_span(client, None) == expected.total_seconds()


async def test_calc_default_life_span_invalid(
    caplog: Any, monkeypatch: Any, tmp_path: Path, make_client: _MakeClient,
) -> None:
    async with make_client("https://example.com") as client:
        monkeypatch.chdir(tmp_path)
        local_conf = tmp_path / ".neuro.toml"
        # empty config
        local_conf.write_text(toml.dumps({"job": {"life-span": "invalid"}}))
        with pytest.raises(
            click.UsageError, match="Could not parse job timeout",
        ):
            await calc_life_span(client, None)


async def test_calc_default_life_span_default_value(
    caplog: Any, monkeypatch: Any, tmp_path: Path, make_client: _MakeClient,
) -> None:
    async with make_client("https://example.com") as client:
        monkeypatch.chdir(tmp_path)
        local_conf = tmp_path / ".neuro.toml"
        # empty config
        local_conf.write_text(toml.dumps({}))
        default = _parse_timedelta(DEFAULT_JOB_LIFE_SPAN)
        assert await calc_life_span(client, None) == default.total_seconds()


def test_parse_timedelta_valid_zero() -> None:
    assert _parse_timedelta("0") == timedelta(0)


def test_parse_timedelta_valid_all_groups_no_spaces() -> None:
    expected = timedelta(days=1, hours=2, minutes=3, seconds=4)
    assert _parse_timedelta("1d2h3m4s") == expected


def test_parse_timedelta_valid_all_groups_spaces_around() -> None:
    expected = timedelta(days=1, hours=2, minutes=3, seconds=4)
    assert _parse_timedelta("  1d2h3m4s ") == expected


def test_parse_timedelta_valid_some_groups_1() -> None:
    expected = timedelta(days=1, hours=2, seconds=4)
    assert _parse_timedelta("1d2h4s") == expected


def test_parse_timedelta_valid_some_groups_2() -> None:
    expected = timedelta(days=1, hours=1)
    assert _parse_timedelta("1d1h") == expected


def test_parse_timedelta_valid_some_groups_3() -> None:
    expected = timedelta(days=1)
    assert _parse_timedelta("1d") == expected


def test_parse_timedelta_invalid_empty() -> None:
    with pytest.raises(click.UsageError, match="Empty string not allowed"):
        _parse_timedelta("")


def test_parse_timedelta_invalid() -> None:
    with pytest.raises(click.UsageError, match="Should be like"):
        _parse_timedelta("invalid")


def test_parse_timedelta_invalid_negative() -> None:
    with pytest.raises(click.UsageError, match="Should be like"):
        _parse_timedelta("-1d")


def test_parse_cmd_single() -> None:
    cmd = ["bash -c 'ls -l && pwd'"]
    assert _parse_cmd(cmd) == "bash -c 'ls -l && pwd'"


def test_parse_cmd_multiple() -> None:
    cmd = ["bash", "-c", "ls -l && pwd"]
    assert _parse_cmd(cmd) == "bash -c 'ls -l && pwd'"
