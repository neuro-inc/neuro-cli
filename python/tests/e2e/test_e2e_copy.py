import os
from pathlib import PurePath

import pytest

from neuromation.client import FileStatusType
from tests.e2e.utils import FILE_SIZE_B, output_to_files


@pytest.mark.e2e
def test_copy_local_to_platform_single_file_0(helper, data):
    srcfile, checksum = data
    file_name = str(PurePath(srcfile).name)

    helper.check_create_dir_on_storage("folder")
    # Upload local file to existing directory
    # case when copy happens with the trailing '/'
    helper.check_upload_file_to_storage(None, "folder/", srcfile)  # tmpstorage/

    # Ensure file is there
    helper.check_file_exists_on_storage(file_name, "folder", FILE_SIZE_B)

    # Remove the file from platform
    helper.check_rm_file_on_storage(file_name, "folder")

    # Ensure file is not there
    helper.check_file_absent_on_storage(file_name, "folder")


@pytest.mark.e2e
def test_copy_local_to_platform_single_file_1(helper, data):
    # case when copy happens without the trailing '/'
    srcfile, checksum = data
    file_name = str(PurePath(srcfile).name)

    helper.check_create_dir_on_storage("folder")

    # Upload local file to existing directory
    helper.check_upload_file_to_storage(None, "folder", srcfile)

    # Ensure file is there
    helper.check_file_exists_on_storage(file_name, "folder", FILE_SIZE_B)

    # Remove the file from platform
    helper.check_rm_file_on_storage(file_name, "folder")

    # Ensure file is not there
    helper.check_file_absent_on_storage(file_name, "folder")


@pytest.mark.e2e
def test_copy_local_to_platform_single_file_2(data, run_cli):
    # case when copy happens with rename to 'different_name.txt'
    srcfile, checksum = data
    file_name = str(PurePath(srcfile).name)

    helper.check_create_dir_on_storage("folder")
    # Upload local file to existing directory
    helper.check_upload_file_to_storage("different_name.txt", "folder", srcfile)

    # Ensure file is there
    helper.check_file_exists_on_storage("different_name.txt", "folder", FILE_SIZE_B)
    helper.check_file_absent_on_storage(file, "folder")

    # Remove the file from platform
    helper.check_rm_file_on_storage("different_name.txt", "folder")

    # Ensure file is not there
    helper.check_file_absent_on_storage("different_name.txt", "folder")


@pytest.mark.e2e
def test_copy_local_to_platform_single_file_3(helper, data, run_cli):
    # case when copy happens with rename to 'different_name.txt'
    srcfile, checksum = data

    # Upload local file to non existing directory
    with pytest.raises(SystemExit, match=str(os.EX_OSFILE)):
        captured = run_cli(
            ["storage", "cp", srcfile, helper.tmpstorage + "/non_existing_dir/"],
            storage_retry=False,
        )
        assert not captured.err
        assert captured.out == ""

    # Ensure dir is not created
    helper.check_dir_absent_on_storage("non_existing_dir", "")


@pytest.mark.e2e
def test_e2e_copy_non_existing_platform_to_non_existing_local(
    helper, run_cli, tmp_path
):
    # Try downloading non existing file
    with pytest.raises(SystemExit, match=str(os.EX_OSFILE)):
        run_cli(
            [
                "storage",
                "cp",
                helper.tmpstorage + "/not-exist-foo",
                str(tmp_path / "not-exist-bar"),
            ],
            storage_retry=False,
        )


@pytest.mark.e2e
def test_e2e_copy_non_existing_platform_to_____existing_local(
    helper, run_cli, tmp_path
):
    # Try downloading non existing file
    with pytest.raises(SystemExit, match=str(os.EX_OSFILE)):
        run_cli(
            ["storage", "cp", helper.tmpstorage + "/foo", str(tmp_path)],
            storage_retry=False,
        )
