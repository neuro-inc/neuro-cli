from datetime import timedelta

import click
import pytest

from neuro_cli.parse_utils import (
    PS_COLUMNS_MAP,
    SORT_KEY_FUNCS,
    JobColumnInfo,
    get_default_ps_columns,
    get_default_top_columns,
    parse_memory,
    parse_ps_columns,
    parse_sort_keys,
    parse_timedelta,
    parse_top_columns,
)


def test_parse_memory() -> None:
    for value in ["1234", "   ", "", "-124", "M", "K", "k", "123B"]:
        with pytest.raises(ValueError, match=f"Unable parse value: {value}"):
            parse_memory(value)

    assert parse_memory("1K") == 1024
    assert parse_memory("2K") == 2048
    assert parse_memory("1k") == 1024
    assert parse_memory("2k") == 2048
    assert parse_memory("1kB") == 1000
    assert parse_memory("2kB") == 2000
    assert parse_memory("1kb") == 1000
    assert parse_memory("2kb") == 2000

    assert parse_memory("42M") == 42 * 1024 ** 2
    assert parse_memory("42MB") == 42 * 1000 ** 2
    assert parse_memory("42Mb") == 42 * 1000 ** 2

    assert parse_memory("42G") == 42 * 1024 ** 3
    assert parse_memory("42GB") == 42 * 1000 ** 3
    assert parse_memory("42Gb") == 42 * 1000 ** 3

    assert parse_memory("42T") == 42 * 1024 ** 4
    assert parse_memory("42TB") == 42 * 1000 ** 4
    assert parse_memory("42Tb") == 42 * 1000 ** 4

    assert parse_memory("42P") == 42 * 1024 ** 5
    assert parse_memory("42PB") == 42 * 1000 ** 5
    assert parse_memory("42Pb") == 42 * 1000 ** 5

    assert parse_memory("42E") == 42 * 1024 ** 6
    assert parse_memory("42EB") == 42 * 1000 ** 6
    assert parse_memory("42Eb") == 42 * 1000 ** 6

    assert parse_memory("42Z") == 42 * 1024 ** 7
    assert parse_memory("42ZB") == 42 * 1000 ** 7
    assert parse_memory("42Zb") == 42 * 1000 ** 7

    assert parse_memory("42Y") == 42 * 1024 ** 8
    assert parse_memory("42YB") == 42 * 1000 ** 8
    assert parse_memory("42Yb") == 42 * 1000 ** 8


def test_parse_ps_columns_default() -> None:
    default_columns = get_default_ps_columns()
    assert parse_ps_columns("") == default_columns
    assert parse_ps_columns(None) == default_columns


def test_parse_top_columns_default() -> None:
    default_columns = get_default_top_columns()
    assert parse_top_columns("") == default_columns
    assert parse_top_columns(None) == default_columns


def test_parse_ps_columns_short() -> None:
    ci = PS_COLUMNS_MAP["id"]
    assert parse_ps_columns("{id}") == [
        JobColumnInfo("id", ci.title, ci.justify, ci.width, ci.min_width, ci.max_width)
    ]


def test_parse_ps_columns_id() -> None:
    ci = PS_COLUMNS_MAP["id"]
    assert parse_ps_columns("id") == [
        JobColumnInfo("id", ci.title, ci.justify, ci.width, ci.min_width, ci.max_width)
    ]


def test_parse_ps_columns_partial() -> None:
    ci = PS_COLUMNS_MAP["description"]
    assert parse_ps_columns("{DESC}") == [
        JobColumnInfo(
            "desc", ci.title, ci.justify, ci.width, ci.min_width, ci.max_width
        )
    ]


def test_parse_ps_columns_sep() -> None:
    ci1 = PS_COLUMNS_MAP["id"]
    ci2 = PS_COLUMNS_MAP["name"]
    expected = [
        JobColumnInfo(
            "id", ci1.title, ci1.justify, ci1.width, ci1.min_width, ci1.max_width
        ),
        JobColumnInfo(
            "name", ci2.title, ci2.justify, ci2.width, ci2.min_width, ci2.max_width
        ),
    ]
    assert parse_ps_columns("{id}{name}") == expected
    assert parse_ps_columns("{id} {name}") == expected
    assert parse_ps_columns("{id},{name}") == expected
    assert parse_ps_columns("{id} ,{name}") == expected
    assert parse_ps_columns("{id}, {name}") == expected
    assert parse_ps_columns("{id} , {name}") == expected

    assert parse_ps_columns("id name") == expected
    assert parse_ps_columns("id,name") == expected
    assert parse_ps_columns("id ,name") == expected
    assert parse_ps_columns("id, name") == expected
    assert parse_ps_columns("id , name") == expected


def test_parse_ps_columns_title_with_spaces() -> None:
    ci = PS_COLUMNS_MAP["id"]
    assert parse_ps_columns("{id;NEW TITLE}") == [
        JobColumnInfo(
            "id", "NEW TITLE", ci.justify, ci.width, ci.min_width, ci.max_width
        )
    ]


def test_parse_ps_columns_props_full() -> None:
    assert parse_ps_columns("{name;max=30;min=5;align=center;NEW_TITLE}") == [
        JobColumnInfo("name", "NEW_TITLE", "center", min_width=5, max_width=30)
    ]


def test_parse_ps_columns_props_subset() -> None:
    ci = PS_COLUMNS_MAP["name"]
    assert parse_ps_columns("{name;align=center;max=20}") == [
        JobColumnInfo("name", ci.title, "center", max_width=20)
    ]


def test_parse_ps_columns_props_width() -> None:
    ci = PS_COLUMNS_MAP["id"]
    assert parse_ps_columns("{id;max=30;min=5;width=10}") == [
        JobColumnInfo("id", ci.title, ci.justify, width=10, min_width=5, max_width=30)
    ]


def test_parse_ps_columns_multi_id() -> None:
    ci1 = PS_COLUMNS_MAP["id"]
    ci2 = PS_COLUMNS_MAP["name"]
    assert ci1.width is not None
    assert ci1.max_width is None
    assert ci2.width is None
    assert ci2.max_width is not None
    expected = [
        JobColumnInfo(
            "id/name", "ID/NAME", ci1.justify, ci1.width, None, ci2.max_width + 1
        )
    ]
    assert parse_ps_columns("id/name") == expected
    assert parse_ps_columns("{id/name}") == expected
    assert parse_ps_columns("{id/name;ID/NAME}") == expected
    expected = [
        JobColumnInfo(
            "name/id", "NAME/ID", ci2.justify, ci1.width + 1, None, ci2.max_width
        )
    ]
    assert parse_ps_columns("name/id") == expected


def test_parse_ps_columns_multi_id_props_full() -> None:
    ci1 = PS_COLUMNS_MAP["id"]
    assert parse_ps_columns("{id/name;max=30;min=5;align=center;Id (Name)}") == [
        JobColumnInfo("id/name", "Id (Name)", "center", ci1.width, 5, 30)
    ]


def test_parse_ps_columns_invalid_format() -> None:
    with pytest.raises(ValueError, match="Invalid format"):
        parse_ps_columns("{id")


def test_parse_ps_columns_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown column"):
        parse_ps_columns("{unknown}")


def test_parse_ps_columns_invalid_property() -> None:
    with pytest.raises(ValueError, match="Invalid property"):
        parse_ps_columns("{id;min=abc}")


def test_parse_ps_columns_ambigous() -> None:
    with pytest.raises(ValueError, match="Ambiguous column"):
        parse_ps_columns("{c}")


def test_parse_sort_keys() -> None:
    assert parse_sort_keys("name") == [(SORT_KEY_FUNCS["name"], False)]
    assert parse_sort_keys("cpu") == [(SORT_KEY_FUNCS["cpu"], False)]
    assert parse_sort_keys("-cpu") == [(SORT_KEY_FUNCS["cpu"], True)]
    assert parse_sort_keys("name,-cpu,preset") == [
        (SORT_KEY_FUNCS["name"], False),
        (SORT_KEY_FUNCS["cpu"], True),
        (SORT_KEY_FUNCS["preset"], False),
    ]
    with pytest.raises(ValueError, match="invalid sort key"):
        parse_sort_keys("spam")
    with pytest.raises(ValueError, match="invalid sort key"):
        parse_sort_keys("")


def test_parse_timedelta_valid_zero() -> None:
    assert parse_timedelta("0") == timedelta(0)


def test_parse_timedelta_valid_all_groups_no_spaces() -> None:
    expected = timedelta(days=1, hours=2, minutes=3, seconds=4)
    assert parse_timedelta("1d2h3m4s") == expected


def test_parse_timedelta_valid_all_groups_spaces_around() -> None:
    expected = timedelta(days=1, hours=2, minutes=3, seconds=4)
    assert parse_timedelta("  1d2h3m4s ") == expected


def test_parse_timedelta_valid_some_groups_1() -> None:
    expected = timedelta(days=1, hours=2, seconds=4)
    assert parse_timedelta("1d2h4s") == expected


def test_parse_timedelta_valid_some_groups_2() -> None:
    expected = timedelta(days=1, hours=1)
    assert parse_timedelta("1d1h") == expected


def test_parse_timedelta_valid_some_groups_3() -> None:
    expected = timedelta(days=1)
    assert parse_timedelta("1d") == expected


def test_parse_timedelta_invalid_empty() -> None:
    with pytest.raises(click.UsageError, match="Empty string not allowed"):
        parse_timedelta("")


def test_parse_timedelta_invalid() -> None:
    with pytest.raises(click.UsageError, match="Should be like"):
        parse_timedelta("invalid")


def test_parse_timedelta_invalid_negative() -> None:
    with pytest.raises(click.UsageError, match="Should be like"):
        parse_timedelta("-1d")
