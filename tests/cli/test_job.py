import logging
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable, Tuple

import click
import pytest
import toml

from neuromation.api import Client, ConfigError, JobStatus
from neuromation.cli.job import (
    NEUROMATION_ROOT_ENV_VAR,
    _parse_timedelta,
    build_env,
    calc_columns,
    calc_default_life_span,
    calc_life_span,
    calc_statuses,
)
from neuromation.cli.parse_utils import COLUMNS, COLUMNS_MAP


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
        assert await calc_columns(client, None) == COLUMNS


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
        local_conf.write_text(
            toml.dumps(
                {"job": {"default-life-span": {"days": 1, "hours": 2, "minutes": 3}}}
            )
        )
        assert await calc_life_span(client, None) == timedelta(
            days=1, hours=2, minutes=3
        )


async def test_calc_life_span_zero(make_client: _MakeClient) -> None:
    async with make_client("https://example.com") as client:
        assert await calc_life_span(client, "0") == timedelta.max


async def test_calc_life_span_negative(
    monkeypatch: Any, tmp_path: Path, make_client: _MakeClient
) -> None:
    async with make_client("https://example.com") as client:
        monkeypatch.chdir(tmp_path)
        local_conf = tmp_path / ".neuro.toml"
        local_conf.write_text(toml.dumps({"job": {"default-life-span": {"days": -1}}}))
        with pytest.raises(click.UsageError, match="must be non-negative"):
            await calc_life_span(client, None)


def test_parse_timedelta_valid_zero() -> None:
    assert _parse_timedelta("0") == timedelta(0)


def test_parse_timedelta_valid_all_groups_no_spaces() -> None:
    expected = timedelta(days=1, hours=2, minutes=3, seconds=4)
    assert _parse_timedelta("1d2h3m4s") == expected


def test_parse_timedelta_valid_all_groups_all_spaces() -> None:
    expected = timedelta(days=1, hours=2, minutes=3, seconds=4)
    assert _parse_timedelta("1d 2h 3m 4s") == expected


def test_parse_timedelta_valid_all_groups_some_spaces_1() -> None:
    expected = timedelta(days=1, hours=2, minutes=3, seconds=4)
    assert _parse_timedelta("1d 2h3m4s") == expected


def test_parse_timedelta_valid_all_groups_some_spaces_2() -> None:
    expected = timedelta(days=1, hours=2, minutes=3, seconds=4)
    assert _parse_timedelta("1d2h 3m4s") == expected


def test_parse_timedelta_valid_all_groups_some_spaces_3() -> None:
    expected = timedelta(days=1, hours=2, minutes=3, seconds=4)
    assert _parse_timedelta("1d2h3m 4s") == expected


def test_parse_timedelta_valid_all_groups_some_spaces_4() -> None:
    expected = timedelta(days=1, hours=2, minutes=3, seconds=4)
    assert _parse_timedelta("1d 2h3m 4s") == expected


def test_parse_timedelta_valid_all_groups_spaces_around() -> None:
    expected = timedelta(days=1, hours=2, minutes=3, seconds=4)
    assert _parse_timedelta("  1d2h3m4s ") == expected


def test_parse_timedelta_valid_some_groups_1() -> None:
    expected = timedelta(days=1, hours=2, seconds=4)
    assert _parse_timedelta("1d 2h  4s") == expected


def test_parse_timedelta_valid_some_groups_2() -> None:
    expected = timedelta(days=1, hours=1)
    assert _parse_timedelta("1d 1h") == expected


def test_parse_timedelta_invalid_empty() -> None:
    with pytest.raises(click.UsageError, match="Empty string not allowed"):
        _parse_timedelta("")


def test_parse_timedelta_invalid_invalid() -> None:
    with pytest.raises(click.UsageError, match="Should be like"):
        _parse_timedelta("invalid")


async def test_calc_default_life_span_all_keys(
    caplog: Any, monkeypatch: Any, tmp_path: Path, make_client: _MakeClient
) -> None:
    async with make_client("https://example.com") as client:
        monkeypatch.chdir(tmp_path)
        local_conf = tmp_path / ".neuro.toml"
        # empty config
        local_conf.write_text(
            toml.dumps(
                {"job": {"default-life-span": {"days": 1, "hours": 2, "minutes": 3}}}
            )
        )

        assert await calc_default_life_span(client) == timedelta(
            days=1, hours=2, minutes=3
        )


@pytest.mark.parametrize("timeout_key", ["days", "hours", "minutes"])
async def test_calc_default_life_span_some_keys(
    timeout_key: str,
    caplog: Any,
    monkeypatch: Any,
    tmp_path: Path,
    make_client: _MakeClient,
) -> None:
    async with make_client("https://example.com") as client:
        monkeypatch.chdir(tmp_path)
        local_conf = tmp_path / ".neuro.toml"
        # empty config
        local_conf.write_text(
            toml.dumps({"job": {"default-life-span": {timeout_key: 10}}})
        )
        expected = timedelta(**{timeout_key: 10})
        assert await calc_default_life_span(client) == expected


@pytest.mark.parametrize("timeout_key", ["days", "hours", "minutes"])
async def test_calc_default_life_span_invalid_value(
    timeout_key: str,
    caplog: Any,
    monkeypatch: Any,
    tmp_path: Path,
    make_client: _MakeClient,
) -> None:
    async with make_client("https://example.com") as client:
        monkeypatch.chdir(tmp_path)
        local_conf = tmp_path / ".neuro.toml"
        # empty config
        local_conf.write_text(
            toml.dumps({"job": {"default-life-span": {timeout_key: "invalid"}}})
        )
        with pytest.raises(
            ConfigError,
            match=f"invalid type for default-life-span.{timeout_key}, int is expected",
        ):
            await calc_default_life_span(client)


async def test_calc_default_life_span_default_value(
    caplog: Any, monkeypatch: Any, tmp_path: Path, make_client: _MakeClient,
) -> None:
    async with make_client("https://example.com") as client:
        monkeypatch.chdir(tmp_path)
        local_conf = tmp_path / ".neuro.toml"
        # empty config
        local_conf.write_text(toml.dumps({}))
        assert await calc_default_life_span(client) == timedelta(days=1)
