import os
from os.path import join
from pathlib import PurePath

import pytest

from tests.e2e.utils import format_list


FILE_SIZE_MB = 16
FILE_SIZE_B = FILE_SIZE_MB * 1024 * 1024


@pytest.mark.e2e
def test_copy_local_to_platform_single_file_0(
    data,
    remote_and_local,
    check_upload_file_to_storage,
    check_file_exists_on_storage,
    check_rm_file_on_storage,
    check_file_absent_on_storage,
):
    # case when copy happens with the trailing '/'
    _path, _dir = remote_and_local
    file, checksum = data[0]
    file_name = str(PurePath(file).name)

    # Upload local file to existing directory
    check_upload_file_to_storage(None, f"{_path}/", file)

    # Ensure file is there
    check_file_exists_on_storage(file_name, _path, FILE_SIZE_B)

    # Remove the file from platform
    check_rm_file_on_storage(file_name, _path)

    # Ensure file is not there
    check_file_absent_on_storage(file_name, _path)


@pytest.mark.e2e
def test_copy_local_to_platform_single_file_1(
    data,
    remote_and_local,
    check_upload_file_to_storage,
    check_file_exists_on_storage,
    check_rm_file_on_storage,
    check_file_absent_on_storage,
):
    # case when copy happens without the trailing '/'
    _path, _dir = remote_and_local
    file, checksum = data[0]
    file_name = str(PurePath(file).name)

    # Upload local file to existing directory
    check_upload_file_to_storage(None, _path, file)

    # Ensure file is there
    check_file_exists_on_storage(file_name, _path, FILE_SIZE_B)

    # Remove the file from platform
    check_rm_file_on_storage(file_name, _path)

    # Ensure file is not there
    check_file_absent_on_storage(file_name, _path)


@pytest.mark.e2e
def test_copy_local_to_platform_single_file_2(
    data,
    run,
    remote_and_local,
    tmpstorage,
    check_upload_file_to_storage,
    check_file_exists_on_storage,
    check_rm_file_on_storage,
    check_file_absent_on_storage,
):
    # case when copy happens with rename to 'different_name.txt'
    _path, _dir = remote_and_local
    file, checksum = data[0]
    file_name = str(PurePath(file).name)

    # Upload local file to existing directory
    check_upload_file_to_storage("different_name.txt", _path, file)

    # Ensure file is there
    check_file_exists_on_storage("different_name.txt", _path, FILE_SIZE_B)
    captured = run(["store", "ls", tmpstorage + _path + "/"])
    split = captured.out.split("\n")
    assert (
        format_list(name="different_name.txt", size=FILE_SIZE_B, type="file") in split
    )
    assert format_list(name=file_name, size=FILE_SIZE_B, type="file") not in split

    # Remove the file from platform
    check_rm_file_on_storage("different_name.txt", _path)

    # Ensure file is not there
    check_file_absent_on_storage("different_name.txt", _path)


@pytest.mark.e2e
def test_copy_local_to_platform_single_file_3(
    data, run, remote_and_local, tmpstorage, check_dir_absent_on_storage
):
    # case when copy happens with rename to 'different_name.txt'
    _path, _dir = remote_and_local
    file, checksum = data[0]

    # Upload local file to non existing directory
    with pytest.raises(SystemExit, match=str(os.EX_OSFILE)):
        captured = run(["store", "cp", file, tmpstorage + _path + "/non_existing_dir/"])
        assert not captured.err
        assert captured.out == ""

    # Ensure dir is not created
    check_dir_absent_on_storage("non_existing_dir", _path)


@pytest.mark.e2e
def test_e2e_copy_non_existing_platform_to_non_existing_local(
    run, tmpdir, capsys, remote_and_local, tmpstorage
):
    _path, _dir = remote_and_local

    # Try downloading non existing file
    _local = join(tmpdir, "bar")
    with pytest.raises(SystemExit, match=str(os.EX_OSFILE)):
        run(["store", "cp", tmpstorage + _path + "/foo", _local])
    capsys.readouterr()


@pytest.mark.e2e
def test_e2e_copy_non_existing_platform_to_____existing_local(
    run, tmpdir, capsys, remote_and_local, tmpstorage
):
    _path, _dir = remote_and_local

    # Try downloading non existing file
    _local = join(tmpdir)
    with pytest.raises(SystemExit, match=str(os.EX_OSFILE)):
        run(["store", "cp", tmpstorage + _path + "/foo", _local])
    capsys.readouterr()
