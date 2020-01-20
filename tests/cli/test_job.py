import logging
from pathlib import Path
from typing import Any, Callable, Tuple

import click
import pytest
import toml

from neuromation.api import Client, JobStatus
from neuromation.cli.job import (
    NEUROMATION_ROOT_ENV_VAR,
    build_env,
    calc_columns,
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
