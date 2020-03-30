import subprocess
from pathlib import Path, PurePath
from typing import Tuple

import pytest

from neuromation.cli.const import EX_OSFILE
from tests.e2e import Helper
from tests.e2e.utils import FILE_SIZE_B


_Data = Tuple[str, str]


@pytest.mark.e2e
def test_e2e_blob_storage_upload_download(
    data: Tuple[Path, str], tmp_path: Path, helper: Helper, tmp_bucket: str
) -> None:
    srcfile, checksum = data
    key = "folder/foo"

    # Upload local file
    helper.upload_blob(bucket_name=tmp_bucket, key=key, file=srcfile)

    # Confirm file has been uploaded
    helper.check_blob_size(tmp_bucket, key, FILE_SIZE_B)

    # Download into local file and confirm checksum
    helper.check_blob_checksum(tmp_bucket, key, checksum, tmp_path / "bar")


@pytest.mark.e2e
def test_e2e_blob_storage_ls_buckets(helper: Helper, tmp_bucket: str) -> None:
    # Ensure output of ls - empty directory shall print nothing.
    captured = helper.run_cli(["blob", "ls"])
    assert "blob:" + tmp_bucket in captured.out


@pytest.mark.e2e
def test_e2e_blob_storage_ls_blobs_empty_bucket(
    helper: Helper, tmp_bucket: str
) -> None:
    # Ensure output of ls - empty directory shall print nothing.
    captured = helper.run_cli(["blob", "ls", "blob:" + tmp_bucket])
    assert not captured.out


@pytest.mark.e2e
def test_e2e_blob_storage_copy_file_implicit_directory(
    helper: Helper, data: _Data, tmp_bucket: str
) -> None:
    srcfile, checksum = data
    file_name = str(PurePath(srcfile).name)
    key = f"folder/{file_name}"

    # Upload local file to a directory defined by trailing slash
    helper.run_cli(["blob", "cp", srcfile, f"blob:{tmp_bucket}/folder/"])

    # Ensure file is there
    helper.check_blob_size(tmp_bucket, key, FILE_SIZE_B)


@pytest.mark.e2e
def test_e2e_blob_storage_copy_file_explicit_directory(
    helper: Helper, data: _Data, tmp_bucket: str
) -> None:
    srcfile, checksum = data
    file_name = str(PurePath(srcfile).name)
    key = f"folder/{file_name}"

    # Upload local file to existing directory with explocit -t param
    helper.run_cli(["blob", "cp", "-t", f"blob:{tmp_bucket}/folder", srcfile])

    # Ensure file is there
    helper.check_blob_size(tmp_bucket, key, FILE_SIZE_B)


@pytest.mark.e2e
def test_e2e_blob_storage_copy_file_to_folder_key(
    helper: Helper, data: _Data, tmp_bucket: str
) -> None:
    srcfile, checksum = data
    file_name = str(PurePath(srcfile).name)
    stub_key = "folder/bar"
    key = f"folder/{file_name}"
    folder_uri = f"blob:{tmp_bucket}/folder"

    # First upload to a nested path
    helper.upload_blob(bucket_name=tmp_bucket, key=stub_key, file=srcfile)

    # Second will succeed, but upload the file `under` the `folder`,
    # as it's a folder key
    helper.run_cli(["blob", "cp", srcfile, folder_uri])
    helper.check_blob_size(tmp_bucket, stub_key, FILE_SIZE_B)
    helper.check_blob_size(tmp_bucket, key, FILE_SIZE_B)

    # Second we do the same command, but with -T that should raise an error
    with pytest.raises(
        subprocess.CalledProcessError,
        match=f"returned non-zero exit status {EX_OSFILE}",
    ):
        helper.run_cli(["blob", "cp", "-T", srcfile, folder_uri])


@pytest.mark.e2e
def test_e2e_blob_storage_copy_no_sources_no_destination(helper: Helper) -> None:
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(["blob", "cp"])
    assert 'Missing argument "DESTINATION"' in cm.value.stderr


@pytest.mark.e2e
def test_e2e_blob_storage_copy_no_sources(helper: Helper) -> None:
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(["blob", "cp", "blob:foo"])
    assert 'Missing argument "SOURCES..."' in cm.value.stderr


@pytest.mark.e2e
def test_e2e_blob_storage_copy_no_sources_target_directory(helper: Helper) -> None:
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(["blob", "cp", "-t", "blob:foo"])
    assert 'Missing argument "SOURCES..."' in cm.value.stderr


@pytest.mark.e2e
def test_e2e_blob_storage_copy_target_directory_no_target_directory(
    helper: Helper, tmp_path: Path
) -> None:
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(["blob", "cp", "-t", "blob:foo", "-T", str(tmp_path)])
    assert "Cannot combine" in cm.value.stderr


@pytest.mark.e2e
def test_e2e_blob_storage_copy_no_target_directory_extra_operand(
    helper: Helper, tmp_path: Path
) -> None:
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(["blob", "cp", "-T", str(tmp_path), "blob:foo", str(tmp_path)])
    assert "Extra operand after " in cm.value.stderr


@pytest.mark.e2e
def test_e2e_blob_storage_copy_recursive(
    helper: Helper, nested_data: Tuple[str, str, str], tmp_path: Path, tmp_bucket: str
) -> None:
    srcfile, checksum, dir_path = nested_data
    target_file_name = Path(srcfile).name

    # Upload local folder .../neested_data/nested to bucket root
    captured = helper.run_cli(["blob", "cp", "-r", dir_path, f"blob:{tmp_bucket}"])
    # stderr has logs like "Using path ..."
    # assert not captured.err
    assert not captured.out

    helper.check_blob_size(
        tmp_bucket, f"nested/directory/for/test/{target_file_name}", FILE_SIZE_B
    )

    # Download into local directory and confirm checksum
    targetdir = tmp_path / "bar"
    targetdir.mkdir()
    helper.run_cli(["blob", "cp", "-r", f"blob:{tmp_bucket}/", str(targetdir)])
    targetfile = targetdir / "nested" / "directory" / "for" / "test" / target_file_name
    print("source file", srcfile)
    print("target file", targetfile)
    assert helper.hash_hex(targetfile) == checksum
