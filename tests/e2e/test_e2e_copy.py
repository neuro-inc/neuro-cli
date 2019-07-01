import os
import subprocess
from pathlib import Path, PurePath
from typing import Tuple

import pytest

from neuromation.cli.const import EX_OSFILE
from tests.e2e import Helper
from tests.e2e.utils import FILE_SIZE_B


_Data = Tuple[str, str]


@pytest.mark.e2e
def test_copy_local_file_to_platform_directory(helper: Helper, data: _Data) -> None:
    srcfile, checksum = data
    file_name = str(PurePath(srcfile).name)

    helper.check_create_dir_on_storage("folder")
    # Upload local file to existing directory
    helper.run_cli(["storage", "cp", srcfile, helper.tmpstorage + "/folder"])

    # Ensure file is there
    helper.check_file_exists_on_storage(file_name, "folder", FILE_SIZE_B)

    # Remove the file from platform
    helper.check_rm_file_on_storage(file_name, "folder")

    # Ensure file is not there
    helper.check_file_absent_on_storage(file_name, "folder")


@pytest.mark.e2e
def test_copy_local_file_to_platform_directory_explicit(
    helper: Helper, data: _Data
) -> None:
    srcfile, checksum = data
    file_name = str(PurePath(srcfile).name)

    helper.check_create_dir_on_storage("folder")
    # Upload local file to existing directory
    helper.run_cli(["storage", "cp", "-t", helper.tmpstorage + "/folder", srcfile])

    # Ensure file is there
    helper.check_file_exists_on_storage(file_name, "folder", FILE_SIZE_B)

    # Remove the file from platform
    helper.check_rm_file_on_storage(file_name, "folder")

    # Ensure file is not there
    helper.check_file_absent_on_storage(file_name, "folder")


@pytest.mark.e2e
def test_copy_local_single_file_to_platform_file(helper: Helper, data: _Data) -> None:
    # case when copy happens with rename to 'different_name.txt'
    srcfile, checksum = data
    file_name = str(PurePath(srcfile).name)

    helper.check_create_dir_on_storage("folder")
    # Upload local file to platform
    helper.run_cli(
        ["storage", "cp", srcfile, helper.tmpstorage + "/folder/different_name.txt"]
    )

    # Ensure file is there
    helper.check_file_exists_on_storage("different_name.txt", "folder", FILE_SIZE_B)
    helper.check_file_absent_on_storage(file_name, "folder")

    # Remove the file from platform
    helper.check_rm_file_on_storage("different_name.txt", "folder")

    # Ensure file is not there
    helper.check_file_absent_on_storage("different_name.txt", "folder")


@pytest.mark.e2e
def test_copy_local_single_file_to_platform_file_explicit(
    helper: Helper, data: _Data
) -> None:
    # case when copy happens with rename to 'different_name.txt'
    srcfile, checksum = data
    file_name = str(PurePath(srcfile).name)

    helper.check_create_dir_on_storage("folder")
    # Upload local file to platform
    helper.run_cli(
        [
            "storage",
            "cp",
            "-T",
            srcfile,
            helper.tmpstorage + "/folder/different_name.txt",
        ]
    )

    # Ensure file is there
    helper.check_file_exists_on_storage("different_name.txt", "folder", FILE_SIZE_B)
    helper.check_file_absent_on_storage(file_name, "folder")

    # Remove the file from platform
    helper.check_rm_file_on_storage("different_name.txt", "folder")

    # Ensure file is not there
    helper.check_file_absent_on_storage("different_name.txt", "folder")


@pytest.mark.e2e
def test_copy_local_to_platform_single_file_3(helper: Helper, data: _Data) -> None:
    # case when copy happens with rename to 'different_name.txt'
    srcfile, checksum = data

    # Upload local file to non existing directory
    with pytest.raises(subprocess.CalledProcessError, match=str(EX_OSFILE)):
        captured = helper.run_cli(
            ["storage", "cp", srcfile, helper.tmpstorage + "/non_existing_dir/"]
        )
        assert not captured.err
        assert captured.out == ""

    # Ensure dir is not created
    helper.check_dir_absent_on_storage("non_existing_dir", "")


@pytest.mark.e2e
def test_e2e_copy_non_existing_platform_to_non_existing_local(
    helper: Helper, tmp_path: Path
) -> None:
    # Try downloading non existing file
    with pytest.raises(subprocess.CalledProcessError, match=str(EX_OSFILE)):
        helper.run_cli(
            [
                "storage",
                "cp",
                helper.tmpstorage + "/not-exist-foo",
                str(tmp_path / "not-exist-bar"),
            ]
        )


@pytest.mark.e2e
def test_e2e_copy_non_existing_platform_to_____existing_local(
    helper: Helper, tmp_path: Path
) -> None:
    # Try downloading non existing file
    with pytest.raises(subprocess.CalledProcessError, match=str(EX_OSFILE)):
        helper.run_cli(["storage", "cp", helper.tmpstorage + "/foo", str(tmp_path)])


@pytest.mark.e2e
def test_e2e_copy_no_sources_no_destination(helper: Helper) -> None:
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(["storage", "cp"])
    assert 'Missing argument "DESTINATION"' in cm.value.stderr


@pytest.mark.e2e
def test_e2e_copy_no_sources(helper: Helper) -> None:
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(["storage", "cp", helper.tmpstorage])
    assert 'Missing argument "SOURCES..."' in cm.value.stderr


@pytest.mark.e2e
def test_e2e_copy_no_sources_target_directory(helper: Helper) -> None:
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(["storage", "cp", "-t", helper.tmpstorage])
    assert 'Missing argument "SOURCES..."' in cm.value.stderr


@pytest.mark.e2e
def test_e2e_copy_target_directory_no_target_directory(
    helper: Helper, tmp_path: Path
) -> None:
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(["storage", "cp", "-t", helper.tmpstorage, "-T", str(tmp_path)])
    assert "Cannot combine" in cm.value.stderr


@pytest.mark.e2e
def test_copy_and_remove_multiple_files(
    helper: Helper, data: _Data, data2: _Data, tmp_path: Path
) -> None:
    # case when copy happens with rename to 'different_name.txt'
    srcfile, checksum = data
    srcfile2, checksum2 = data2
    srcname = os.path.basename(srcfile)
    srcname2 = os.path.basename(srcfile2)

    # Upload local files
    captured = helper.run_cli(["storage", "cp", srcfile, srcfile2, helper.tmpstorage])
    assert captured.out == ""

    # Confirm files has been uploaded
    helper.check_file_exists_on_storage(srcname, "", FILE_SIZE_B)
    helper.check_file_exists_on_storage(srcname2, "", FILE_SIZE_B // 3)

    # Download into local directory and confirm checksum
    targetdir = tmp_path / "bar"
    targetdir.mkdir()
    helper.run_cli(
        [
            "storage",
            "cp",
            f"{helper.tmpstorage}/{srcname}",
            f"{helper.tmpstorage}/{srcname2}",
            str(targetdir),
        ]
    )
    assert helper.hash_hex(targetdir / srcname) == checksum
    assert helper.hash_hex(targetdir / srcname2) == checksum2

    # Remove the files from platform
    captured = helper.run_cli(
        [
            "storage",
            "rm",
            f"{helper.tmpstorage}/{srcname}",
            f"{helper.tmpstorage}/{srcname2}",
        ]
    )
    assert captured.out == ""

    # Ensure files are not there
    helper.check_file_absent_on_storage(srcname, "")
    helper.check_file_absent_on_storage(srcname2, "")
