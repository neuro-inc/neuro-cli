import asyncio
import platform
import re
from math import ceil
from os.path import join
from time import sleep, time
from uuid import uuid4 as uuid

import pytest

from tests.e2e.test_e2e_utils import wait_for_job_to_change_state_to
from tests.e2e.utils import (
    UBUNTU_IMAGE_NAME,
    attempt,
    check_create_dir_on_storage,
    check_dir_absent_on_storage,
    check_file_exists_on_storage,
    check_file_on_storage_checksum,
    check_rename_directory_on_storage,
    check_rename_file_on_storage,
    check_rmdir_on_storage,
    check_upload_file_to_storage,
    hash_hex,
    try_or_assert,
)


BLOCK_SIZE_MB = 16
FILE_COUNT = 1
FILE_SIZE_MB = 16
FILE_SIZE_B = FILE_SIZE_MB * 1024 * 1024
GENERATION_TIMEOUT_SEC = 120
RC_TEXT = "url: http://platform.dev.neuromation.io/api/v1\n" "auth: {token}"


async def generate_test_data(root, count, size_mb):
    async def generate_file(name):
        exec_sha_name = "sha1sum" if platform.platform() == "linux" else "shasum"

        process = await asyncio.create_subprocess_shell(
            f"""(dd if=/dev/urandom \
                    bs={BLOCK_SIZE_MB * 1024 * 1024} \
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
def test_empty_directory_ls_output(run):
    _dir = f"e2e-{uuid()}"
    _path = f"/tmp/{_dir}"

    # Create directory for the test
    _, captured = run(["store", "mkdir", f"storage://{_path}"])
    assert not captured.err
    assert captured.out == f"storage://{_path}\n"

    # Ensure output of ls - empty directory shall print nothing.
    def dir_must_be_empty():
        _, captured = run(["store", "ls", f"storage://{_path}"])
        assert not captured.err
        assert captured.out.isspace()

    try_or_assert(dir_must_be_empty)

    # Remove test dir
    _, captured = run(["store", "rm", f"storage://{_path}"])
    assert not captured.err


@pytest.mark.e2e
def test_e2e_shm_run_without(run, tmpdir):
    _dir_src = f"e2e-{uuid()}"
    _path_src = f"/tmp/{_dir_src}"

    _dir_dst = f"e2e-{uuid()}"
    _path_dst = f"/tmp/{_dir_dst}"

    # Create directory for the test, going to be model and result output
    run(["store", "mkdir", f"storage://{_path_src}"])
    run(["store", "mkdir", f"storage://{_path_dst}"])

    # Start the df test job
    bash_script = "/bin/df --block-size M --output=target,avail /dev/shm; false"
    command = f"bash -c '{bash_script}'"
    _, captured = run(
        [
            "model",
            "train",
            "-m",
            "20M",
            "-c",
            "0.1",
            "-g",
            "0",
            UBUNTU_IMAGE_NAME,
            "storage://" + _path_src,
            "storage://" + _path_dst,
            command,
        ]
    )

    # TODO (R Zubairov, 09/13/2018): once we would have wait for job
    # replace spin loop

    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)
    start_time = time()
    while ("Status: failed" not in out) and (int(time() - start_time) < 10):
        sleep(2)
        _, captured = run(["job", "status", job_id])
        out = captured.out

    # Remove test dir
    run(["store", "rm", f"storage://{_path_src}"])
    run(["store", "rm", f"storage://{_path_dst}"])

    assert "/dev/shm" in out
    assert "64M" in out


@pytest.mark.e2e
def test_e2e_shm_run_with(run, tmpdir):
    _dir_src = f"e2e-{uuid()}"
    _path_src = f"/tmp/{_dir_src}"

    _dir_dst = f"e2e-{uuid()}"
    _path_dst = f"/tmp/{_dir_dst}"

    # Create directory for the test, going to be model and result output
    run(["store", "mkdir", f"storage://{_path_src}"])
    run(["store", "mkdir", f"storage://{_path_dst}"])

    # Start the df test job
    bash_script = "/bin/df --block-size M ' '--output=target,avail /dev/shm; false"
    command = f"bash -c {bash_script}"
    _, captured = run(
        [
            "model",
            "train",
            "-x",
            "-m",
            "20M",
            "-c",
            "0.1",
            "-g",
            "0",
            UBUNTU_IMAGE_NAME,
            "storage://" + _path_src,
            "storage://" + _path_dst,
            command,
        ]
    )

    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)
    wait_for_job_to_change_state_to(run, job_id, "Status: failed")

    # Remove test dir
    run(["store", "rm", f"storage://{_path_src}"])
    run(["store", "rm", f"storage://{_path_dst}"])

    _, captured = run(["job", "status", job_id])
    out = captured.out

    assert "/dev/shm" in out
    assert "64M" not in out


@pytest.mark.e2e
def test_e2e(data, run, tmpdir):
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
    check_file_on_storage_checksum(run, "foo", _path, checksum, tmpdir, "bar")

    # Download into local dir and confirm checksum
    @attempt()
    def check_file_on_storage_checksum_custom_download():
        _local = join(tmpdir, "bardir")
        _local_file = join(_local, "foo")
        tmpdir.mkdir("bardir")
        _, captured = run(["store", "cp", f"storage://{_path}/foo", _local])
        assert hash_hex(_local_file) == checksum

    check_file_on_storage_checksum_custom_download()

    # Rename file on the storage
    check_rename_file_on_storage(run, "foo", _path, "bar", _path)

    # Confirm file has been renamed
    check_file_exists_on_storage(run, "bar", _path, FILE_SIZE_B)

    # Rename directory on the storage
    _dir2 = f"e2e-{uuid()}"
    _path2 = f"/tmp/{_dir2}"
    check_rename_directory_on_storage(run, _path, _path2)

    # Remove test dir
    check_rmdir_on_storage(run, _path2)

    # And confirm
    check_dir_absent_on_storage(run, _dir, "/tmp")
