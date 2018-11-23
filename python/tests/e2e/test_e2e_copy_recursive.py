from functools import partial
from os.path import join
from pathlib import PurePath
from uuid import uuid4 as uuid

import pytest

from tests.e2e.conftest import hash_hex
from tests.e2e.utils import format_list, try_or_assert


@pytest.mark.e2e
def test_e2e_copy_recursive_to_platform(nested_data, run, tmpdir):
    file, checksum, dir_path = nested_data

    target_file_name = file.split("/")[-1]
    _dir = f"e2e-{uuid()}"
    _path = f"/tmp/{_dir}"
    dir_name = PurePath(dir_path).name

    # Create directory for the test
    _, captured = run(["store", "mkdir", f"storage://{_path}"])
    assert not captured.err
    assert captured.out == f"storage://{_path}" + "\n"

    # Upload local file
    _, captured = run(["store", "cp", "-r", dir_path, "storage://" + _path + "/"])
    assert not captured.err
    assert _path in captured.out

    def directory_exists_in_path(path, directory):
        _, captured = run(["store", "ls", f"storage://{path}"])
        captured_output_list = captured.out.split("\n")
        assert f"directory      0              {directory}" in captured_output_list
        assert not captured.err

    # Check directory structure
    try_or_assert(partial(directory_exists_in_path, _path, dir_name))
    try_or_assert(partial(directory_exists_in_path, f"{_path}/{dir_name}", "nested"))
    try_or_assert(
        partial(directory_exists_in_path, f"{_path}/{dir_name}/nested", "directory")
    )
    try_or_assert(
        partial(directory_exists_in_path, f"{_path}/{dir_name}/nested/directory", "for")
    )
    try_or_assert(
        partial(
            directory_exists_in_path, f"{_path}/{dir_name}/nested/directory/for", "test"
        )
    )

    # Confirm file has been uploaded
    def file_must_be_uploaded():
        _, captured = run(
            ["store", "ls", f"storage://{_path}/{dir_name}/nested/directory/for/test"]
        )
        captured_output_list = captured.out.split("\n")
        assert (
            f"file           16,777,216     {target_file_name}" in captured_output_list
        )
        assert not captured.err

    try_or_assert(file_must_be_uploaded)

    # Download into local directory and confirm checksum
    def downloaded_file_must_have_same_hash():
        tmpdir.mkdir("bar")
        _local = join(tmpdir, "bar")
        _, captured = run(["store", "cp", "-r", f"storage://{_path}/", _local])
        assert (
            hash_hex(
                f"{_local}/{_dir}/{dir_name}"
                f"/nested/directory/for/test/{target_file_name}"
            )
            == checksum
        )

    try_or_assert(downloaded_file_must_have_same_hash)

    # Remove test dir
    _, captured = run(["store", "rm", f"storage://{_path}"])
    assert not captured.err

    # And confirm
    def temporary_dir_must_be_empty():
        _, captured = run(["store", "ls", f"storage:///tmp"])
        split = captured.out.split("\n")
        assert format_list(name=_dir, size=0, type="directory") not in split
        assert not captured.err

    try_or_assert(temporary_dir_must_be_empty)
