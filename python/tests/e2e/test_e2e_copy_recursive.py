import pytest

from tests.e2e.utils import FILE_SIZE_B


@pytest.mark.e2e
def test_e2e_copy_recursive_to_platform(helper, nested_data, tmp_path):
    srcfile, checksum, dir_path = nested_data
    target_file_name = srcfile.split("/")[-1]

    # Upload local file
    captured = helper.run_cli(["storage", "cp", "-r", dir_path, helper.tmpstorage])
    # stderr has logs like "Using path ..."
    # assert not captured.err
    assert not captured.out

    helper.check_file_exists_on_storage(
        target_file_name, f"nested/directory/for/test", FILE_SIZE_B
    )

    # Download into local directory and confirm checksum

    targetdir = tmp_path / "bar"
    targetdir.mkdir()
    helper.run_cli(["storage", "cp", "-r", f"{helper.tmpstorage}", str(targetdir)])
    targetfile = targetdir / "nested" / "directory" / "for" / "test" / target_file_name
    print("source file", srcfile)
    print("target file", targetfile)
    assert helper.hash_hex(targetfile) == checksum

    # Remove test dir
    helper.check_rmdir_on_storage("nested")

    # And confirm
    helper.check_dir_absent_on_storage("nested", "")
