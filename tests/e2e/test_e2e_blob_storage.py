from typing import Tuple

import pytest

from tests.e2e import Helper


_Data = Tuple[str, str]


# @pytest.mark.e2e
# def test_e2e_blob_storage_upload_download(
#     data: Tuple[Path, str], tmp_path: Path, helper: Helper, tmp_bucket: str
# ) -> None:
#     srcfile, checksum = data
#     key = "folder/foo"

#     # Upload local file
#     helper.upload_blob(bucket_name=tmp_bucket, key=key, file=srcfile)

#     # Confirm file has been uploaded
#     helper.check_blob_size(tmp_bucket, key, FILE_SIZE_B)

#     # Download into local file and confirm checksum
#     helper.check_blob_checksum(tmp_bucket, key, checksum, tmp_path / "bar")


@pytest.mark.e2e
def test_blob_storage_ls_buckets(helper: Helper, tmp_bucket: str) -> None:
    # Ensure output of ls - empty directory shall print nothing.
    captured = helper.run_cli(["blob", "ls"])
    assert "blob:" + tmp_bucket in captured.out


@pytest.mark.e2e
def test_blob_storage_ls_blobs_empty_bucket(helper: Helper, tmp_bucket: str) -> None:
    # Ensure output of ls - empty directory shall print nothing.
    captured = helper.run_cli(["blob", "ls", "blob:" + tmp_bucket])
    assert not captured.out
