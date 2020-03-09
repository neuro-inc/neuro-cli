import sqlite3
from unittest import mock

import pytest

import neuromation
from neuromation.cli.stats import (
    SCHEMA,
    add_usage,
    delete_oldest,
    ensure_schema,
    select_oldest,
)


@pytest.fixture
def db() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    return db


def check_tables(db: sqlite3.Connection) -> None:
    tables = {}

    for name, sql in db.execute(
        "SELECT name, sql from sqlite_master WHERE type='table'"
    ):
        tables[name] = sql

    assert tables == SCHEMA


def test_ensure_schema_empty(db: sqlite3.Connection) -> None:
    ensure_schema(db)
    check_tables(db)


def test_ensure_schema_invalid(db: sqlite3.Connection) -> None:
    db.execute("CREATE TABLE stats (invalid INTEGER)")
    ensure_schema(db)
    check_tables(db)


def test_add_usage(db: sqlite3.Connection) -> None:
    ensure_schema(db)
    add_usage(db, "neuro run", [{}, {"-s": "cpu-small", "image": None, "cmd": None}])
    add_usage(
        db,
        "neuro ps",
        [{}, {"-s": "('failed', 'running')", "image": None, "cmd": None}],
    )
    ret = list(db.execute("SELECT cmd, args, version FROM stats"))
    assert len(ret) == 2
    assert dict(ret[0]) == {
        "cmd": "neuro run",
        "args": '[{}, {"-s": "cpu-small", "image": null, "cmd": null}]',
        "version": neuromation.__version__,
    }
    assert dict(ret[1]) == {
        "cmd": "neuro ps",
        "args": '[{}, {"-s": "(\'failed\', \'running\')", "image": null, "cmd": null}]',
        "version": neuromation.__version__,
    }


def test_select_oldest(db: sqlite3.Connection) -> None:
    ensure_schema(db)
    add_usage(db, "neuro run", [{}, {"-s": "cpu-small", "image": None, "cmd": None}])
    add_usage(
        db,
        "neuro ps",
        [{}, {"-s": "('failed', 'running')", "image": None, "cmd": None}],
    )
    old = select_oldest(db, limit=1)
    assert len(old) == 1
    assert dict(old[0]) == {
        "rowid": mock.ANY,
        "cmd": "neuro run",
        "args": '[{}, {"-s": "cpu-small", "image": null, "cmd": null}]',
        "timestamp": mock.ANY,
        "version": neuromation.__version__,
    }


def test_delete_oldest(db: sqlite3.Connection) -> None:
    ensure_schema(db)
    add_usage(db, "neuro run", [{}, {"-s": "cpu-small", "image": None, "cmd": None}])
    add_usage(
        db,
        "neuro ps",
        [{}, {"-s": "('failed', 'running')", "image": None, "cmd": None}],
    )
    old = select_oldest(db, limit=1)
    delete_oldest(db, old)
    ret = list(db.execute("SELECT cmd, args, version FROM stats"))
    assert len(ret) == 1
    assert dict(ret[0]) == {
        "cmd": "neuro ps",
        "args": '[{}, {"-s": "(\'failed\', \'running\')", "image": null, "cmd": null}]',
        "version": neuromation.__version__,
    }
