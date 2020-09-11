import pytest

from neuromation.cli.formatters.ftable import Align, ColumnWidth
from neuromation.cli.parse_utils import (
    COLUMNS_MAP,
    JobColumnInfo,
    get_default_columns,
    parse_columns,
    parse_memory,
)


def test_parse_memory() -> None:
    for value in ["   ", "", "-124", "-22M", "K", "k"]:
        with pytest.raises(ValueError, match=f"Unable parse value: {value}"):
            parse_memory(value)

    assert parse_memory("100") == 100
    assert parse_memory("200") == 200

    assert parse_memory("1 K") == 1000
    assert parse_memory("2  K") == 2000
    assert parse_memory("1   k") == 1000
    assert parse_memory("2 k") == 2000
    assert parse_memory("1 Ki") == 1024
    assert parse_memory("2   Ki") == 2048
    assert parse_memory("1 KiB") == 1024
    assert parse_memory("2 KiB") == 2048

    assert parse_memory("42M") == 42 * 1000 ** 2
    assert parse_memory("42Mi") == 42 * 1024 ** 2
    assert parse_memory("42MiB") == 42 * 1024 ** 2

    assert parse_memory("42G") == 42 * 1000 ** 3
    assert parse_memory("42Gi") == 42 * 1024 ** 3
    assert parse_memory("42GiB") == 42 * 1024 ** 3

    assert parse_memory("42G") == 42 * 1000 ** 3
    assert parse_memory("42Gi") == 42 * 1024 ** 3
    assert parse_memory("42GiB") == 42 * 1024 ** 3

    assert parse_memory("42T") == 42 * 1000 ** 4
    assert parse_memory("42Ti") == 42 * 1024 ** 4
    assert parse_memory("42TiB") == 42 * 1024 ** 4

    assert parse_memory("42P") == 42 * 1000 ** 5
    assert parse_memory("42Pi") == 42 * 1024 ** 5
    assert parse_memory("42PiB") == 42 * 1024 ** 5

    assert parse_memory("42E") == 42 * 1000 ** 6
    assert parse_memory("42Ei") == 42 * 1024 ** 6
    assert parse_memory("42EiB") == 42 * 1024 ** 6


def test_parse_columns_default() -> None:
    default_columns = get_default_columns()
    assert parse_columns("") == default_columns
    assert parse_columns(None) == default_columns


def test_parse_columns_short() -> None:
    ci = COLUMNS_MAP["id"]
    assert parse_columns("{id}") == [JobColumnInfo("id", ci.title, ci.align, ci.width)]


def test_parse_columns_id() -> None:
    ci = COLUMNS_MAP["id"]
    assert parse_columns("id") == [JobColumnInfo("id", ci.title, ci.align, ci.width)]


def test_parse_columns_partial() -> None:
    ci = COLUMNS_MAP["description"]
    assert parse_columns("{DESC}") == [
        JobColumnInfo("description", ci.title, ci.align, ci.width)
    ]


def test_parse_columns_sep() -> None:
    ci1 = COLUMNS_MAP["id"]
    ci2 = COLUMNS_MAP["name"]
    expected = [
        JobColumnInfo("id", ci1.title, ci1.align, ci1.width),
        JobColumnInfo("name", ci2.title, ci2.align, ci2.width),
    ]
    assert parse_columns("{id}{name}") == expected
    assert parse_columns("{id} {name}") == expected
    assert parse_columns("{id},{name}") == expected
    assert parse_columns("{id} ,{name}") == expected
    assert parse_columns("{id}, {name}") == expected
    assert parse_columns("{id} , {name}") == expected

    assert parse_columns("id name") == expected
    assert parse_columns("id,name") == expected
    assert parse_columns("id ,name") == expected
    assert parse_columns("id, name") == expected
    assert parse_columns("id , name") == expected


def test_parse_columns_title_with_spaces() -> None:
    ci = COLUMNS_MAP["id"]
    assert parse_columns("{id;NEW TITLE}") == [
        JobColumnInfo("id", "NEW TITLE", ci.align, ci.width)
    ]


def test_parse_columns_props_full() -> None:
    assert parse_columns("{id;max=30;min=5;align=center;NEW_TITLE}") == [
        JobColumnInfo("id", "NEW_TITLE", Align.CENTER, ColumnWidth(5, 30))
    ]


def test_parse_columns_props_subset() -> None:
    ci = COLUMNS_MAP["name"]
    assert parse_columns("{name;align=center;max=20}") == [
        JobColumnInfo("name", ci.title, Align.CENTER, ColumnWidth(None, 20))
    ]


def test_parse_columns_props_width() -> None:
    ci = COLUMNS_MAP["id"]
    assert parse_columns("{id;max=30;min=5;width=10}") == [
        JobColumnInfo("id", ci.title, ci.align, ColumnWidth(10, 10, 10))
    ]


def test_parse_columns_invalid_format() -> None:
    with pytest.raises(ValueError, match="Invalid format"):
        parse_columns("{id")


def test_parse_columns_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown column"):
        parse_columns("{unknown}")


def test_parse_columns_invalid_property() -> None:
    with pytest.raises(ValueError, match="Invalid property"):
        parse_columns("{id;min=abc}")


def test_parse_columns_ambigous() -> None:
    with pytest.raises(ValueError, match="Ambiguous column"):
        parse_columns("{c}")
