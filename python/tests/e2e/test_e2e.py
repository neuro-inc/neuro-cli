import re
from time import sleep

import pytest

import neuromation
from neuromation.client import FileStatusType
from tests.e2e.test_e2e_utils import (
    Status,
    assert_job_state,
    wait_job_change_state_from,
    wait_job_change_state_to,
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
    assert "API URL: https://dev.neu.ro/api/v1" in captured.out


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
def test_e2e_job_top(run):
    def split_non_empty_parts(line, separator=None):
        return [part.strip() for part in line.split(separator) if part.strip()]

    bash_script = "sleep 10m"
    command = f"bash -c '{bash_script}'"
    captured = run(["job", "submit", UBUNTU_IMAGE_NAME, command, "--quiet"])
    job_id = captured.out.strip()
    wait_job_change_state_from(run, job_id, "Status: pending")

    captured = run(["job", "top", job_id])

    header_line, top_line = split_non_empty_parts(captured.out, separator="\n")
    header_parts = split_non_empty_parts(header_line, separator="\t")
    assert header_parts == [
        "TIMESTAMP",
        "CPU",
        "MEMORY (MB)",
        "GPU (%)",
        "GPU_MEMORY (MB)",
    ]

    line_parts = split_non_empty_parts(top_line, separator="\t")
    timestamp_pattern_parts = [
        ("weekday", "[A-Z][a-z][a-z]"),
        ("month", "[A-Z][a-z][a-z]"),
        ("day", r"\d+"),
        ("day", r"\d\d:\d\d:\d\d"),
        ("year", "2019"),
    ]
    timestamp_pattern = r"\s+".join([part[1] for part in timestamp_pattern_parts])
    expected_parts = [
        ("timestamp", timestamp_pattern),
        ("cpu", r"\d.\d\d\d"),
        ("memory", r"\d.\d\d\d"),
        ("gpu", "0"),
        ("gpu memory", "0"),
    ]
    for actual, (description, pattern) in zip(line_parts, expected_parts):
        assert re.match(pattern, actual) is not None, f"error in matching {description}"


@pytest.mark.e2e
@pytest.mark.parametrize(
    "switch,expected",
    [["--extshm", True], ["--no-extshm", False], [None, True]],  # default is enabled
)
def test_e2e_shm_switch(switch, expected, run):
    # Start the df test job
    bash_script = "/bin/df --block-size M --output=target,avail /dev/shm | grep 64M"
    command = f"bash -c '{bash_script}'"
    arguments = [
        "job",
        "submit",
        "-m",
        "20M",
        "-c",
        "0.1",
        "-g",
        "0",
        "--non-preemptible",
    ]
    if switch is not None:
        arguments.append(switch)
    arguments += [UBUNTU_IMAGE_NAME, command]
    captured = run(arguments)

    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)
    if expected:
        wait_job_change_state_to(run, job_id, Status.FAILED, Status.SUCCEEDED)
    else:
        wait_job_change_state_to(run, job_id, Status.SUCCEEDED, Status.FAILED)


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
