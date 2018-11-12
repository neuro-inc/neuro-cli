from os.path import join
from pathlib import PurePath
from uuid import uuid4 as uuid

import pytest

from tests.e2e.conftest import hash_hex
from tests.e2e.utils import format_list


@pytest.mark.e2e
def test_e2e_copy_recursive_to_platform(nested_data, run, tmpdir):
    file, checksum, dir_path = nested_data

    target_file_name = file.split("/")[-1]
    _dir = f"e2e-{uuid()}"
    _path = f"/tmp/{_dir}"
    dir_name = PurePath(_path).name

    # Create directory for the test
    _, captured = run(["store", "mkdir", f"storage://{_path}"])
    assert not captured.err
    assert captured.out == f"storage://{_path}" + "\n"

    # Upload local file
    _, captured = run(["store", "cp", "-r", dir_path, "storage://" + _path + "/"])
    assert not captured.err
    assert _path in captured.out

    # Check directory structure
    _, captured = run(["store", "ls", f"storage://{_path}"])
    captured_output_list = captured.out.split("\n")
    assert f"directory      0              data1" in captured_output_list
    assert not captured.err

    _, captured = run(["store", "ls", f"storage://{_path}/data1"])
    captured_output_list = captured.out.split("\n")
    assert f"directory      0              nested" in captured_output_list
    assert not captured.err

    _, captured = run(["store", "ls", f"storage://{_path}/data1/nested"])
    captured_output_list = captured.out.split("\n")
    assert f"directory      0              directory" in captured_output_list
    assert not captured.err

    _, captured = run(["store", "ls", f"storage://{_path}/data1/nested/directory"])
    captured_output_list = captured.out.split("\n")
    assert f"directory      0              for" in captured_output_list
    assert not captured.err

    _, captured = run(["store", "ls", f"storage://{_path}/data1/nested/directory/for"])
    captured_output_list = captured.out.split("\n")
    assert f"directory      0              test" in captured_output_list
    assert not captured.err

    # Confirm file has been uploaded
    _, captured = run(
        ["store", "ls", f"storage://{_path}/data1/nested/directory/for/test"]
    )
    captured_output_list = captured.out.split("\n")
    assert f"file           16,777,216     {target_file_name}" in captured_output_list
    assert not captured.err

    # Download into local directory and confirm checksum
    tmpdir.mkdir("bar")
    _local = join(tmpdir, "bar")
    _, captured = run(["store", "cp", "-r", f"storage://{_path}/", _local])
    assert (
        hash_hex(
            f"{_local}/{dir_name}/data1/nested/directory/for/test/{target_file_name}"
        )
        == checksum
    )

    # Remove test dir
    _, captured = run(["store", "rm", f"storage://{_path}"])
    assert not captured.err

    # And confirm
    _, captured = run(["store", "ls", f"storage:///tmp"])

    split = captured.out.split("\n")
    assert format_list(name=_dir, size=0, type="directory") not in split

    assert not captured.err
