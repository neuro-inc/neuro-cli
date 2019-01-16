from os.path import join
from pathlib import PurePath
from uuid import uuid4 as uuid

import pytest

from tests.e2e.utils import (
    FILE_SIZE_MB,
    check_create_dir_on_storage,
    check_dir_absent_on_storage,
    check_dir_exists_on_storage,
    check_file_exists_on_storage,
    check_rmdir_on_storage,
    hash_hex,
)


FILE_SIZE_B = FILE_SIZE_MB * 1024 * 1024


@pytest.mark.e2e
def test_e2e_copy_recursive_to_platform(nested_data, run, tmpdir):
    file, checksum, dir_path = nested_data

    target_file_name = file.split("/")[-1]
    _dir = f"e2e-{uuid()}"
    _path = f"/tmp/{_dir}"
    dir_name = PurePath(dir_path).name

    # Create directory for the test
    check_create_dir_on_storage(run, _path)

    # Upload local file
    captured = run(["store", "cp", "-r", dir_path, "storage://" + _path + "/"])
    assert not captured.err
    assert not captured.out

    check_dir_exists_on_storage(run, dir_name, _path)
    check_dir_exists_on_storage(run, "nested", f"{_path}/{dir_name}")
    check_dir_exists_on_storage(run, "directory", f"{_path}/{dir_name}/nested")
    check_dir_exists_on_storage(run, "for", f"{_path}/{dir_name}/nested/directory")
    check_dir_exists_on_storage(run, "test", f"{_path}/{dir_name}/nested/directory/for")

    check_file_exists_on_storage(
        run,
        target_file_name,
        f"{_path}/{dir_name}/nested/directory/for/test",
        FILE_SIZE_B,
    )

    # Download into local directory and confirm checksum
    def recursive_download_and_check_cheksum():
        target = f"bar-{uuid()}"
        tmpdir.mkdir(target)
        _local = join(tmpdir, target)
        run(["store", "cp", "-r", f"storage://{_path}/", _local])
        assert (
            hash_hex(
                f"{_local}/{_dir}/{dir_name}"
                f"/nested/directory/for/test/{target_file_name}"
            )
            == checksum
        )

    recursive_download_and_check_cheksum()

    # Remove test dir
    check_rmdir_on_storage(run, _path)

    # And confirm
    check_dir_absent_on_storage(run, _path, "/tmp")
