import re
from time import sleep

import pytest

import neuromation
from neuromation.client import FileStatusType
from tests.e2e.test_e2e_utils import (
    Status,
    assert_job_state,
    wait_job_change_state_from,
)
from tests.e2e.utils import FILE_SIZE_B, UBUNTU_IMAGE_NAME, output_to_files


@pytest.mark.e2e
def test_print_version(run):
    expected_out = f"Neuromation Platform Client {neuromation.__version__}"

    captured = run(["--version"])
    assert not captured.err
    assert captured.out == expected_out


@pytest.mark.e2e
def test_print_config(run):
    captured = run(["config", "show"])
    assert not captured.err
    assert "API URL: https://platform.dev.neuromation.io/api/v1" in captured.out


@pytest.mark.e2e
def test_print_config_token(run):
    captured = run(["config", "show-token"])
    assert not captured.err
    assert captured.out  # some secure information was printed


@pytest.mark.e2e
def test_empty_directory_ls_output(run, tmpstorage):
    # Ensure output of ls - empty directory shall print nothing.
    captured = run(["storage", "ls", tmpstorage])
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
            "--non-preemptible",
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
            "--non-preemptible",
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
    srcfile, checksum = data

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
    captured = run(["storage", "ls", "-l", f"{tmpstorage}folder"])
    assert not captured.err
    files = output_to_files(captured.out)
    for file in files:
        if file.name == "bar" and file.type == FileStatusType.FILE:
            break
    else:
        raise AssertionError("File bar not found after renaming from foo")
    for file in files:
        if file.name == "foo" and file.type == FileStatusType.FILE:
            raise AssertionError("File foo still on storage after renaming to bar")

    # Rename directory on the storage
    check_rename_directory_on_storage("folder", "folder2")

    # Remove test dir
    check_rmdir_on_storage("folder2")

    # And confirm
    check_dir_absent_on_storage("folder2", "")


@pytest.mark.e2e
def test_job_storage_interaction(
    run,
    data,
    tmpstorage,
    tmp_path,
    check_create_dir_on_storage,
    check_upload_file_to_storage,
    check_file_on_storage_checksum,
    check_file_exists_on_storage,
):
    srcfile, checksum = data
    # Create directory for the test
    check_create_dir_on_storage("data")

    # Upload local file
    check_upload_file_to_storage("foo", "data", str(srcfile))

    delay = 0.5
    for i in range(5):
        # Run a job to copy file
        command = "cp /data/foo /res/foo"
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
                "--http",
                "80",
                "--volume",
                f"{tmpstorage}data:/data:ro",
                "--volume",
                f"{tmpstorage}result:/res:rw",
                "--non-preemptible",
                UBUNTU_IMAGE_NAME,
                command,
            ]
        )
        job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)

        # Wait for job to finish
        wait_job_change_state_from(run, job_id, Status.PENDING)
        wait_job_change_state_from(run, job_id, Status.RUNNING)
        try:
            assert_job_state(run, job_id, Status.SUCCEEDED)
            # Confirm file has been copied
            check_file_exists_on_storage("foo", "", FILE_SIZE_B)

            # Download into local dir and confirm checksum
            check_file_on_storage_checksum("foo", "result", checksum, tmp_path, "bar")

            break
        except AssertionError:
            sleep(delay)
            delay *= 2
