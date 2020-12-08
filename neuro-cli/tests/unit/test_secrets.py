import pathlib

from neuro_cli.secrets import read_data


def test_read_data_str() -> None:
    assert b"value" == read_data("value")


def test_read_data_file(tmp_path: pathlib.Path) -> None:
    fname = tmp_path / "secret.txt"
    fname.write_bytes(b"file content")
    assert b"file content" == read_data("@" + str(fname))
