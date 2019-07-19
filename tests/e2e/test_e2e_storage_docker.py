import sys
from pathlib import Path, PurePath
from typing import Tuple

import pytest

from tests.e2e import Helper
from tests.e2e.utils import FILE_SIZE_B


_Data = Tuple[str, str]


@pytest.mark.skipif(
    sys.platform == "win32", reason="Docker is not configured on Windows"
)
@pytest.mark.e2e
def test_load_local_file_to_platform_home_directory(
    helper: Helper, data: _Data
) -> None:
    srcfile, checksum = data
    file_name = str(PurePath(srcfile).name)

    captured = helper.run_cli(["storage", "load", srcfile, "storage:"])
    print(f"nero stdout: {captured.out}")
    print(f"nero stderr: {captured.err}")

    # Ensure file is there
    helper.check_file_exists_on_storage(file_name, "", FILE_SIZE_B, fromhome=True)

    # Remove the file from platform
    helper.check_rm_file_on_storage(file_name, "", fromhome=True)


@pytest.mark.skipif(
    sys.platform == "win32", reason="Docker is not configured on Windows"
)
@pytest.mark.e2e
def test_load_local_file_to_platform_directory(helper: Helper, data: _Data) -> None:
    srcfile, checksum = data
    file_name = str(PurePath(srcfile).name)

    helper.check_create_dir_on_storage("folder")
    # Upload local file to existing directory
    captured = helper.run_cli(
        ["storage", "load", srcfile, helper.tmpstorage + "/folder"]
    )
    print(f"nero stdout: {captured.out}")
    print(f"nero stderr: {captured.err}")

    # Ensure file is there
    helper.check_file_exists_on_storage(file_name, "folder", FILE_SIZE_B)

    # Remove the file from platform
    helper.check_rm_file_on_storage(file_name, "folder")

    # Ensure file is not there
    helper.check_file_absent_on_storage(file_name, "folder")


@pytest.mark.skipif(
    sys.platform == "win32", reason="Docker is not configured on Windows"
)
@pytest.mark.e2e
def test_load_local_single_file_to_platform_file(helper: Helper, data: _Data) -> None:
    # case when copy happens with rename to 'different_name.txt'
    srcfile, checksum = data
    file_name = str(PurePath(srcfile).name)

    helper.check_create_dir_on_storage("folder")
    # Upload local file to platform
    captured = helper.run_cli(
        ["storage", "load", srcfile, helper.tmpstorage + "/folder/different_name.txt"]
    )
    print(f"nero stdout: {captured.out}")
    print(f"nero stderr: {captured.err}")

    # Ensure file is there
    helper.check_file_exists_on_storage("different_name.txt", "folder", FILE_SIZE_B)
    helper.check_file_absent_on_storage(file_name, "folder")

    # Remove the file from platform
    helper.check_rm_file_on_storage("different_name.txt", "folder")

    # Ensure file is not there
    helper.check_file_absent_on_storage("different_name.txt", "folder")


@pytest.mark.skipif(
    sys.platform == "win32", reason="Docker is not configured on Windows"
)
@pytest.mark.e2e
def test_e2e_load_recursive_to_platform(
    helper: Helper, nested_data: Tuple[str, str, str], tmp_path: Path
) -> None:
    srcfile, checksum, dir_path = nested_data
    target_file_name = Path(srcfile).name

    # Upload local file
    captured = helper.run_cli(["storage", "load", "-r", dir_path, helper.tmpstorage])
    print(f"nero stdout: {captured.out}")
    print(f"nero stderr: {captured.err}")

    helper.check_file_exists_on_storage(
        target_file_name, f"nested/directory/for/test", FILE_SIZE_B
    )

    # Download into local directory and confirm checksum
    targetdir = tmp_path / "bar"
    targetdir.mkdir()
    captured = helper.run_cli(
        ["storage", "load", "-r", f"{helper.tmpstorage}", str(targetdir)]
    )
    print(f"nero stdout: {captured.out}")
    print(f"nero stderr: {captured.err}")
    targetfile = targetdir / "nested" / "directory" / "for" / "test" / target_file_name
    print("source file", srcfile)
    print("target file", targetfile)
    assert str(targetfile) in list(map(str, targetdir.rglob("*")))
    assert helper.hash_hex(targetfile) == checksum

    # Remove test dir
    helper.check_rmdir_on_storage("nested")

    # And confirm
    helper.check_dir_absent_on_storage("nested", "")
