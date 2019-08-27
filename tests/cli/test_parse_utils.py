import pytest

from neuromation.cli.parse_utils import parse_memory


def test_parse_memory() -> None:
    for value in ["1234", "   ", "", "-124", "M", "K", "k", "123B"]:
        with pytest.raises(ValueError, match=f"Unable parse value: {value}"):
            parse_memory(value)

    assert parse_memory("1K") == 1024
    assert parse_memory("2K") == 2048
    assert parse_memory("1kB") == 1000
    assert parse_memory("2kB") == 2000

    assert parse_memory("42M") == 42 * 1024 ** 2
    assert parse_memory("42MB") == 42 * 1000 ** 2

    assert parse_memory("42G") == 42 * 1024 ** 3
    assert parse_memory("42GB") == 42 * 1000 ** 3

    assert parse_memory("42T") == 42 * 1024 ** 4
    assert parse_memory("42TB") == 42 * 1000 ** 4

    assert parse_memory("42P") == 42 * 1024 ** 5
    assert parse_memory("42PB") == 42 * 1000 ** 5

    assert parse_memory("42E") == 42 * 1024 ** 6
    assert parse_memory("42EB") == 42 * 1000 ** 6

    assert parse_memory("42Z") == 42 * 1024 ** 7
    assert parse_memory("42ZB") == 42 * 1000 ** 7

    assert parse_memory("42Y") == 42 * 1024 ** 8
    assert parse_memory("42YB") == 42 * 1000 ** 8
