import logging
from typing import Any, Tuple

import click
import pytest

from neuromation.api import JobStatus
from neuromation.cli.job import calc_statuses


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
