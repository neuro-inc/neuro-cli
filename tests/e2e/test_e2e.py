import re
from uuid import uuid4

import pytest

import neuromation
from neuromation.client import JobStatus
from tests.e2e.utils import FILE_SIZE_B, JOB_TINY_CONTAINER_PARAMS, UBUNTU_IMAGE_NAME


@pytest.mark.e2e
def test_print_version(helper):
    expected_out = f"Neuromation Platform Client {neuromation.__version__}"

    captured = helper.run_cli(["--version"])
    assert not captured.err
    assert captured.out == expected_out


@pytest.mark.e2e
def test_print_options(helper):
    captured = helper.run_cli(["--options"])
    assert not captured.err
    assert "Options" in captured.out


@pytest.mark.e2e
def test_print_config(helper):
    captured = helper.run_cli(["config", "show"])
    assert not captured.err
    assert "API URL: https://dev.neu.ro/api/v1" in captured.out


@pytest.mark.e2e
def test_print_config_token(helper):
    captured = helper.run_cli(["config", "show-token"])
    assert not captured.err
    assert captured.out  # some secure information was printed


@pytest.mark.e2e
def test_empty_directory_ls_output(helper):
    # Ensure output of ls - empty directory shall print nothing.
    captured = helper.run_cli(["storage", "ls", helper.tmpstorage])
    assert not captured.out


@pytest.mark.e2e
def test_e2e_job_top(helper):
    def split_non_empty_parts(line, separator=None):
        return [part.strip() for part in line.split(separator) if part.strip()]

    bash_script = (
        "COUNTER=0; while [[ ! -f /data/dummy ]] && [[ $COUNTER -lt 100 ]]; "
        "do sleep 1; let COUNTER+=1; done; sleep 30"
    )
    command = f"bash -c '{bash_script}'"
    job_name = f"test-job-{uuid4()}"
    aux_params = ["--volume", f"{helper.tmpstorage}:/data:ro", "--name", job_name]

    helper.run_job_and_wait_state(
        image=UBUNTU_IMAGE_NAME,
        command=command,
        params=JOB_TINY_CONTAINER_PARAMS + aux_params,
    )

    # the job is running
    # upload a file and unblock the job
    helper.check_upload_file_to_storage("dummy", "", __file__)

    captured = helper.run_cli(["job", "top", job_name])

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
def test_e2e_shm_switch(switch, expected, helper):
    # Start the df test job
    bash_script = "/bin/df --block-size M --output=target,avail /dev/shm | grep 64M"
    command = f"bash -c '{bash_script}'"
    params = [] + JOB_TINY_CONTAINER_PARAMS
    if switch is not None:
        params.append(switch)

    if expected:
        job_id = helper.run_job_and_wait_state(
            UBUNTU_IMAGE_NAME, command, params, JobStatus.FAILED, JobStatus.SUCCEEDED
        )
        status = helper.job_info(job_id)
        assert re.search(r"Exit code: 1", status.history.description)
    else:
        helper.run_job_and_wait_state(
            UBUNTU_IMAGE_NAME, command, params, JobStatus.SUCCEEDED, JobStatus.FAILED
        )


@pytest.mark.e2e
def test_e2e_storage(data, tmp_path, helper):
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
def test_job_storage_interaction(helper, data, tmp_path):
    srcfile, checksum = data
    # Create directory for the test
    helper.check_create_dir_on_storage("data")

    # Upload local file
    helper.check_upload_file_to_storage("foo", "data", str(srcfile))

    command = "cp /data/foo /res/foo"

    helper.run_job_and_wait_state(
        UBUNTU_IMAGE_NAME,
        command,
        JOB_TINY_CONTAINER_PARAMS
        + [
            "--volume",
            f"{helper.tmpstorage}data:/data:ro",
            "--volume",
            f"{helper.tmpstorage}result:/res:rw",
        ],
        JobStatus.SUCCEEDED,
        JobStatus.FAILED,
    )

    # Download into local dir and confirm checksum
    helper.check_file_on_storage_checksum("foo", "result", checksum, tmp_path, "bar")
