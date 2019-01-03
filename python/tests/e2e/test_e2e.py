import asyncio
import platform
import re
import time
from math import ceil
from os.path import join
from uuid import uuid4 as uuid

import pytest

import neuromation
from tests.e2e.test_e2e_utils import assert_job_state, wait_job_change_state_from
from tests.e2e.utils import (
    UBUNTU_IMAGE_NAME,
    check_create_dir_on_storage,
    check_dir_absent_on_storage,
    check_file_exists_on_storage,
    check_file_on_storage_checksum,
    check_rename_directory_on_storage,
    check_rename_file_on_storage,
    check_rmdir_on_storage,
    check_upload_file_to_storage,
    format_list,
    hash_hex,
)


BLOCK_SIZE_MB = 16
BLOCK_SIZE_B = BLOCK_SIZE_MB * 1024 * 1024
FILE_COUNT = 1
FILE_SIZE_MB = 16
FILE_SIZE_B = FILE_SIZE_MB * 1024 * 1024
GENERATION_TIMEOUT_SEC = 120
RC_TEXT = "url: https://platform.dev.neuromation.io/api/v1\n" "auth: {token}"


async def generate_test_data(root, count, size_mb):
    async def generate_file(name):
        exec_sha_name = "sha1sum" if platform.platform() == "linux" else "shasum"

        process = await asyncio.create_subprocess_shell(
            f"""(dd if=/dev/urandom \
                    bs={BLOCK_SIZE_B} \
                    count={ceil(size_mb / BLOCK_SIZE_MB)} \
                    2>/dev/null) | \
                    tee {name} | \
                    {exec_sha_name}""",
            stdout=asyncio.subprocess.PIPE,
        )

        stdout, _ = await asyncio.wait_for(
            process.communicate(), timeout=GENERATION_TIMEOUT_SEC
        )

        # sha1sum appends file name to the output
        return name, stdout.decode()[:40]

    return await asyncio.gather(
        *[
            generate_file(join(root, name))
            for name in (str(uuid()) for _ in range(count))
        ]
    )


@pytest.fixture(scope="session")
def data(tmpdir_factory):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        generate_test_data(tmpdir_factory.mktemp("data"), FILE_COUNT, FILE_SIZE_MB)
    )


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
def test_empty_directory_ls_output(run, remote_and_local):
    _path, _dir = remote_and_local

    # Ensure output of ls - empty directory shall print nothing.
    captured = run(["store", "ls", f"storage://{_path}"])
    assert not captured.err
    assert not captured.out


@pytest.mark.e2e
def test_e2e_shm_run_without(run, tmpdir):
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
def test_e2e_shm_run_with(run, tmpdir):
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
def test_e2e_storage(data, run, tmpdir):
    file, checksum = data[0]

    _dir = f"e2e-{uuid()}"
    _path = f"/tmp/{_dir}"

    # Create directory for the test
    check_create_dir_on_storage(run, _path)

    # Upload local file
    check_upload_file_to_storage(run, "foo", _path, file)

    # Confirm file has been uploaded
    check_file_exists_on_storage(run, "foo", _path, FILE_SIZE_B)

    # Download into local file and confirm checksum
    exc = None
    delay = 5
    for i in range(5):
        try:
            check_file_on_storage_checksum(run, "foo", _path, checksum, tmpdir, "bar")
            break
        except AssertionError as e:
            exc = e
            time.sleep(delay)
            delay *= 2
    else:
        raise exc

    # Download into deeper local dir and confirm checksum
    localdir = f"bardir-{uuid()}"
    _local = join(tmpdir, localdir)
    _local_file = join(_local, "foo")
    tmpdir.mkdir(localdir)
    run(["store", "cp", f"storage://{_path}/foo", _local])
    assert hash_hex(_local_file) == checksum

    # Rename file on the storage
    check_rename_file_on_storage(run, "foo", _path, "bar", _path)

    # Confirm file has been renamed
    captured = run(["store", "ls", f"storage://{_path}"])
    captured_output_list = captured.out.split("\n")
    assert not captured.err
    expected_line = format_list(type="file", size=FILE_SIZE_B, name="bar")
    assert expected_line in captured_output_list
    assert "foo" not in captured_output_list

    # Rename directory on the storage
    _dir2 = f"e2e-{uuid()}"
    _path2 = f"/tmp/{_dir2}"
    check_rename_directory_on_storage(run, _path, _path2)

    # Remove test dir
    check_rmdir_on_storage(run, _path2)

    # And confirm
    check_dir_absent_on_storage(run, _dir, "/tmp")
