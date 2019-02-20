import re
from time import sleep

import pytest

import neuromation
from neuromation.client import JobStatus
from tests.e2e.utils import FILE_SIZE_B, UBUNTU_IMAGE_NAME


@pytest.mark.e2e
def test_print_version(run_cli):
    expected_out = f"Neuromation Platform Client {neuromation.__version__}"

    captured = run_cli(["--version"])
    assert not captured.err
    assert captured.out == expected_out


@pytest.mark.e2e
def test_print_config(run_cli):
    captured = run_cli(["config", "show"])
    assert not captured.err
    assert "API URL: https://dev.neu.ro/api/v1" in captured.out


@pytest.mark.e2e
def test_print_config_token(run_cli):
    captured = run_cli(["config", "show-token"])
    assert not captured.err
    assert captured.out  # some secure information was printed


@pytest.mark.e2e
def test_empty_directory_ls_output(run_cli, helper):
    # Ensure output of ls - empty directory shall print nothing.
    captured = run_cli(["storage", "ls", helper.tmpstorage])
    assert not captured.out
    # FIXME: stderr has "Using path ..." line
    assert len(captured.err.splitlines()) == 1 and captured.err.startswith("Using path")


@pytest.mark.e2e
def test_e2e_job_top(helper, run_cli):
    def split_non_empty_parts(line, separator=None):
        return [part.strip() for part in line.split(separator) if part.strip()]

    bash_script = "sleep 10m"
    command = f"bash -c '{bash_script}'"
    captured = run_cli(["job", "submit", UBUNTU_IMAGE_NAME, command, "--quiet"])
    job_id = captured.out.strip()
    helper.wait_job_change_state_from(job_id, JobStatus.PENDING)

    captured = run_cli(["job", "top", job_id])

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
def test_e2e_shm_run_without(helper, run_cli):
@pytest.mark.parametrize(
    "switch,expected",
    [["--extshm", True], ["--no-extshm", False], [None, True]],  # default is enabled
)
def test_e2e_shm_switch(switch, expected, helper, run_cli):
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
    captured = run_cli(arguments)

    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)
    if expected:
        helper.wait_job_change_state_to(run, job_id, JobStatus.FAILED, JobStatus.SUCCEEDED)
    else:
        helper.wait_job_change_state_to(run, job_id, JobStatus.SUCCEEDED, JobStatus.FAILED)


@pytest.mark.e2e
def test_e2e_storage(data, run_cli, tmp_path, helper):
    srcfile, checksum = data

    # Create directory for the test
    helper.check_create_dir_on_storage("folder")

    # Upload local file
    helper.check_upload_file_to_storage("foo", "folder", str(srcfile))

    # Confirm file has been uploaded
    helper.check_file_exists_on_storage("foo", "folder", FILE_SIZE_B)

    # Download into local file and confirm checksum
    helper.check_file_on_storage_checksum(
        "foo", "folder", checksum, str(tmp_path), "bar"
    )

    # Download into deeper local dir and confirm checksum
    localdir = tmp_path / "baz"
    localdir.mkdir()
    helper.check_file_on_storage_checksum("foo", "folder", checksum, localdir, "foo")

    # Rename file on the storage
    helper.check_rename_file_on_storage("foo", "folder", "bar", "folder")

    # Rename directory on the storage
    helper.check_rename_directory_on_storage("folder", "folder2")

    # Remove test dir
    helper.check_rmdir_on_storage("folder2")

    # And confirm
    helper.check_dir_absent_on_storage("folder2", "")


@pytest.mark.e2e
def test_job_storage_interaction(helper, run_cli, data, tmp_path):
    srcfile, checksum = data
    # Create directory for the test
    helper.check_create_dir_on_storage("data")

    # Upload local file
    helper.check_upload_file_to_storage("foo", "data", str(srcfile))

    delay = 0.5
    for i in range(5):
        # Run a job to copy file
        command = "cp /data/foo /res/foo"
        captured = run_cli(
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
                f"{helper.tmpstorage}data:/data:ro",
                "--volume",
                f"{helper.tmpstorage}result:/res:rw",
                "--non-preemptible",
                UBUNTU_IMAGE_NAME,
                command,
            ]
        )
        job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)

        # Wait for job to finish
        helper.wait_job_change_state_from(job_id, JobStatus.PENDING)
        helper.wait_job_change_state_from(job_id, JobStatus.RUNNING)
        try:
            helper.assert_job_state(job_id, JobStatus.SUCCEEDED)
            # Confirm file has been copied
            helper.check_file_exists_on_storage("foo", "", FILE_SIZE_B)

            # Download into local dir and confirm checksum
            helper.check_file_on_storage_checksum(
                "foo", "result", checksum, tmp_path, "bar"
            )

            break
        except AssertionError:
            sleep(delay)
            delay *= 2
