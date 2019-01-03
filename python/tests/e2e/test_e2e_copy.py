import os
from os.path import join
from pathlib import PurePath
from uuid import uuid4 as uuid

import pytest

from tests.e2e.utils import (
    check_create_dir_on_storage,
    check_dir_absent_on_storage,
    check_file_absent_on_storage,
    check_file_exists_on_storage,
    check_rm_file_on_storage,
    check_rmdir_on_storage,
    check_upload_file_to_storage,
    format_list,
)


FILE_SIZE_MB = 16
FILE_SIZE_B = FILE_SIZE_MB * 1024 * 1024


@pytest.mark.e2e
def test_copy_local_to_platform_single_file_0(data, run, tmpdir, remote_and_local):
    # case when copy happens with the trailing '/'
    _path, _dir = remote_and_local
    file, checksum = data[0]
    file_name = str(PurePath(file).name)

    # Upload local file to existing directory
    check_upload_file_to_storage(run, None, f"{_path}/", file)

    # Ensure file is there
    check_file_exists_on_storage(run, file_name, _path, FILE_SIZE_B)

    # Remove the file from platform
    check_rm_file_on_storage(run, file_name, _path)

    # Ensure file is not there
    check_file_absent_on_storage(run, file_name, _path)


@pytest.mark.e2e
def test_copy_local_to_platform_single_file_1(data, run, tmpdir, remote_and_local):
    # case when copy happens without the trailing '/'
    _path, _dir = remote_and_local
    file, checksum = data[0]
    file_name = str(PurePath(file).name)

    # Upload local file to existing directory
    check_upload_file_to_storage(run, None, _path, file)

    # Ensure file is there
    check_file_exists_on_storage(run, file_name, _path, FILE_SIZE_B)

    # Remove the file from platform
    check_rm_file_on_storage(run, file_name, _path)

    # Ensure file is not there
    check_file_absent_on_storage(run, file_name, _path)


@pytest.mark.e2e
def test_copy_local_to_platform_single_file_2(data, run, tmpdir, remote_and_local):
    # case when copy happens with rename to 'different_name.txt'
    _path, _dir = remote_and_local
    file, checksum = data[0]
    file_name = str(PurePath(file).name)

    # Upload local file to existing directory
    check_upload_file_to_storage(run, "different_name.txt", _path, file)

    # Ensure file is there
    check_file_exists_on_storage(run, "different_name.txt", _path, FILE_SIZE_B)
    captured = run(["store", "ls", "storage://" + _path + "/"])
    split = captured.out.split("\n")
    assert (
        format_list(name="different_name.txt", size=FILE_SIZE_B, type="file") in split
    )
    assert format_list(name=file_name, size=FILE_SIZE_B, type="file") not in split

    # Remove the file from platform
    check_rm_file_on_storage(run, "different_name.txt", _path)

    # Ensure file is not there
    check_file_absent_on_storage(run, "different_name.txt", _path)


@pytest.mark.e2e
def test_copy_local_to_platform_single_file_3(data, run, tmpdir, remote_and_local):
    # case when copy happens with rename to 'different_name.txt'
    _path, _dir = remote_and_local
    file, checksum = data[0]

    # Upload local file to non existing directory
    with pytest.raises(SystemExit, match=str(os.EX_OSFILE)):
        captured = run(
            ["store", "cp", file, "storage://" + _path + "/non_existing_dir/"]
        )
        assert not captured.err
        assert _path in captured.out

    # Ensure dir is not created
    check_dir_absent_on_storage(run, "non_existing_dir", _path)


@pytest.mark.e2e
def test_e2e_copy_non_existing_platform_to_non_existing_local(
    run, tmpdir, capsys, remote_and_local
):
    _path, _dir = remote_and_local

    # Try downloading non existing file
    _local = join(tmpdir, "bar")
    with pytest.raises(SystemExit, match=str(os.EX_OSFILE)):
        run(["store", "cp", "storage://" + _path + "/foo", _local])
    capsys.readouterr()


@pytest.mark.e2e
def test_e2e_copy_non_existing_platform_to_____existing_local(
    run, tmpdir, capsys, remote_and_local
):
    _path, _dir = remote_and_local

    # Try downloading non existing file
    _local = join(tmpdir)
    with pytest.raises(SystemExit, match=str(os.EX_OSFILE)):
        run(["store", "cp", "storage://" + _path + "/foo", _local])
    capsys.readouterr()
