import re

import pytest

import neuromation
from tests.e2e.test_e2e_utils import assert_job_state, wait_job_change_state_from
from tests.e2e.utils import FILE_SIZE_B, UBUNTU_IMAGE_NAME, format_list


@pytest.mark.e2e
@pytest.mark.parametrize("version_key", ["-v", "--version"])
def test_print_version(run, version_key):
    expected_out = f"Neuromation Platform Client {neuromation.__version__}\n"

    captured = run([version_key])
    assert not captured.err
    assert captured.out == expected_out

    captured = run(["job", version_key])
    assert not captured.err
    assert captured.out == expected_out

    captured = run(["job", "submit", "ubuntu", version_key])
    assert not captured.err
    assert captured.out == expected_out


@pytest.mark.e2e
def test_empty_directory_ls_output(run, tmpstorage):
    # Ensure output of ls - empty directory shall print nothing.
    captured = run(["store", "ls", tmpstorage])
    assert not captured.err
    assert not captured.out


@pytest.mark.e2e
def test_e2e_shm_run_without(run):
    # Start the df test job
    bash_script = "/bin/df --block-size M --output=target,avail /dev/shm | grep 64M"
    command = f"bash -c '{bash_script}'"
    captured = run(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "-g",
            "0",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )

    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)
    wait_job_change_state_from(run, job_id, "Status: pending")
    wait_job_change_state_from(run, job_id, "Status: running")

    assert_job_state(run, job_id, "Status: succeeded")


@pytest.mark.e2e
def test_e2e_shm_run_with(run):
    # Start the df test job
    bash_script = "/bin/df --block-size M --output=target,avail /dev/shm | grep 64M"
    command = f"bash -c '{bash_script}'"
    captured = run(
        [
            "job",
            "submit",
            "-x",
            "-m",
            "20M",
            "-c",
            "0.1",
            "-g",
            "0",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)
    wait_job_change_state_from(run, job_id, "Status: pending")
    wait_job_change_state_from(run, job_id, "Status: running")

    assert_job_state(run, job_id, "Status: failed")


@pytest.mark.e2e
def test_e2e_storage(
    data,
    run,
    tmp_path,
    tmpstorage,
    check_create_dir_on_storage,
    check_upload_file_to_storage,
    check_file_exists_on_storage,
    check_file_on_storage_checksum,
    check_rename_file_on_storage,
    check_rename_directory_on_storage,
    check_rmdir_on_storage,
    check_dir_absent_on_storage,
):
    srcfile, checksum = data[0]

    # Create directory for the test
    check_create_dir_on_storage("folder")

    # Upload local file
    check_upload_file_to_storage("foo", "folder", str(srcfile))

    # Confirm file has been uploaded
    check_file_exists_on_storage("foo", "folder", FILE_SIZE_B)

    # Download into local file and confirm checksum
    check_file_on_storage_checksum("foo", "folder", checksum, str(tmp_path), "bar")

    # Download into deeper local dir and confirm checksum
    localdir = tmp_path / "baz"
    localdir.mkdir()
    check_file_on_storage_checksum("foo", "folder", checksum, localdir, "foo")

    # Rename file on the storage
    check_rename_file_on_storage("foo", "folder", "bar", "folder")

    # Confirm file has been renamed
    captured = run(["store", "ls", f"{tmpstorage}folder"])
    captured_output_list = captured.out.split("\n")
    assert not captured.err
    expected_line = format_list(type="file", size=FILE_SIZE_B, name="bar")
    assert expected_line in captured_output_list
    assert "foo" not in captured_output_list

    # Rename directory on the storage
    check_rename_directory_on_storage("folder", "folder2")

    # Remove test dir
    check_rmdir_on_storage("folder2")

    # And confirm
    check_dir_absent_on_storage("folder2", "")
