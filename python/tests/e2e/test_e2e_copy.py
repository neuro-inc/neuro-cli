import os
from os.path import join
from pathlib import PurePath
from uuid import uuid4 as uuid

import pytest

from tests.e2e.utils import format_list


@pytest.mark.e2e
def test_copy_local_to_platform_single_file_0(data, run, tmpdir, remote_and_local):
    # case when copy happens with the trailing '/'
    _path, _dir = remote_and_local
    file, checksum = data[0]
    file_name = str(PurePath(file).name)

    # Upload local file to existing directory
    _, captured = run(["store", "cp", file, "storage://" + _path + "/"])
    assert not captured.err
    assert _path in captured.out

    # Ensure file is there
    _, captured = run(["store", "ls", "storage://" + _path + "/"])
    split = captured.out.split("\n")
    assert format_list(name=file_name, size=16_777_216, type="file") in split

    # Remove the file from platform
    _, captured = run(["store", "rm", f"storage://{_path}/{file_name}"])
    assert not captured.err

    # Ensure file is not there
    _, captured = run(["store", "ls", "storage://" + _path + "/"])
    split = captured.out.split("\n")
    assert format_list(name=file_name, size=16_777_216, type="file") not in split

    # Remove test dir
    _, captured = run(["store", "rm", f"storage://{_path}"])
    assert not captured.err


@pytest.mark.e2e
def test_copy_local_to_platform_single_file_1(data, run, tmpdir, remote_and_local):
    # case when copy happens without the trailing '/'
    _path, _dir = remote_and_local
    file, checksum = data[0]
    file_name = str(PurePath(file).name)

    # Upload local file to existing directory
    _, captured = run(["store", "cp", file, "storage://" + _path])
    assert not captured.err
    assert _path in captured.out

    # Ensure file is there
    _, captured = run(["store", "ls", "storage://" + _path + "/"])
    split = captured.out.split("\n")
    assert format_list(name=file_name, size=16_777_216, type="file") in split

    # Remove the file from platform
    _, captured = run(["store", "rm", f"storage://{_path}/{file_name}"])
    assert not captured.err

    # Ensure file is not there
    _, captured = run(["store", "ls", "storage://" + _path + "/"])
    split = captured.out.split("\n")
    assert format_list(name=file_name, size=16_777_216, type="file") not in split

    # Remove test dir
    _, captured = run(["store", "rm", f"storage://{_path}"])
    assert not captured.err


@pytest.mark.e2e
def test_copy_local_to_platform_single_file_2(data, run, tmpdir, remote_and_local):
    # case when copy happens with rename to 'different_name.txt'
    _path, _dir = remote_and_local
    file, checksum = data[0]
    file_name = str(PurePath(file).name)

    # Upload local file to existing directory
    _, captured = run(
        ["store", "cp", file, "storage://" + _path + "/different_name.txt"]
    )
    assert not captured.err
    assert _path in captured.out

    # Ensure file is there
    _, captured = run(["store", "ls", "storage://" + _path + "/"])
    split = captured.out.split("\n")
    assert format_list(name="different_name.txt", size=16_777_216, type="file") in split
    assert format_list(name=file_name, size=16_777_216, type="file") not in split

    # Remove the file from platform
    _, captured = run(["store", "rm", f"storage://{_path}/different_name.txt"])
    assert not captured.err

    # Ensure file is not there
    _, captured = run(["store", "ls", "storage://" + _path + "/"])
    split = captured.out.split("\n")
    assert (
        format_list(name="different_name.txt", size=16_777_216, type="file")
        not in split
    )
    assert format_list(name=file_name, size=16_777_216, type="file") not in split

    # Remove test dir
    _, captured = run(["store", "rm", f"storage://{_path}"])
    assert not captured.err


@pytest.mark.e2e
def test_copy_local_to_platform_single_file_3(data, run, tmpdir, remote_and_local):
    # case when copy happens with rename to 'different_name.txt'
    _path, _dir = remote_and_local
    file, checksum = data[0]

    # Upload local file to non existing directory
    with pytest.raises(SystemExit, match=str(os.EX_OSFILE)):
        _, captured = run(
            ["store", "cp", file, "storage://" + _path + "/non_existing_dir/"]
        )
        assert not captured.err
        assert _path in captured.out

    # Ensure file is there
    _, captured = run(["store", "ls", "storage://" + _path + "/"])
    split = captured.out.split("\n")
    assert format_list(name="non_existing_dir", size=0, type="directory") not in split

    # Remove test dir
    _, captured = run(["store", "rm", f"storage://{_path}"])
    assert not captured.err


@pytest.mark.e2e
def test_e2e_copy_non_existing_platform_to_non_existing_local(run, tmpdir, capsys):
    _dir = f"e2e-{uuid()}"
    _path = f"/tmp/{_dir}"

    # Create directory for the test
    _, captured = run(["store", "mkdir", f"storage://{_path}"])
    assert not captured.err
    assert captured.out == f"storage://{_path}" + "\n"

    # Try downloading non existing file
    _local = join(tmpdir, "bar")
    with pytest.raises(SystemExit, match=str(os.EX_OSFILE)):
        _, _ = run(["store", "cp", "storage://" + _path + "/foo", _local])
    capsys.readouterr()

    # Remove test dir
    _, captured = run(["store", "rm", f"storage://{_path}"])
    assert not captured.err

    # And confirm
    _, captured = run(["store", "ls", f"storage:///tmp"])

    split = captured.out.split("\n")
    assert format_list(name=_dir, size=0, type="directory") not in split

    assert not captured.err


@pytest.mark.e2e
def test_e2e_copy_non_existing_platform_to_____existing_local(run, tmpdir, capsys):
    _dir = f"e2e-{uuid()}"
    _path = f"/tmp/{_dir}"

    # Create directory for the test
    _, captured = run(["store", "mkdir", f"storage://{_path}"])
    assert not captured.err
    assert captured.out == f"storage://{_path}" + "\n"

    # Try downloading non existing file
    _local = join(tmpdir)
    with pytest.raises(SystemExit, match=str(os.EX_OSFILE)):
        _, captured = run(["store", "cp", "storage://" + _path + "/foo", _local])
    capsys.readouterr()

    # Remove test dir
    _, captured = run(["store", "rm", f"storage://{_path}"])
    assert not captured.err

    # And confirm
    _, captured = run(["store", "ls", f"storage:///tmp"])

    split = captured.out.split("\n")
    assert format_list(name=_dir, size=0, type="directory") not in split

    assert not captured.err
