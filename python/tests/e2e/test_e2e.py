import asyncio
import platform
import re
from os.path import join
from time import sleep, time
from uuid import uuid4 as uuid

import pytest

from tests.e2e.conftest import hash_hex
from tests.e2e.test_e2e_utils import wait_for_job_to_change_state_to
from tests.e2e.utils import UBUNTU_IMAGE_NAME, format_list
from tests.e2e.test_e2e_utils import wait_for_job_to_change_state_to


BLOCK_SIZE_MB = 16
FILE_COUNT = 1
FILE_SIZE_MB = 16
GENERATION_TIMEOUT_SEC = 120
RC_TEXT = "url: http://platform.dev.neuromation.io/api/v1\n" "auth: {token}"

UBUNTU_IMAGE_NAME = "ubuntu:latest"

format_list = "{type:<15}{size:<15,}{name:<}".format


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


def hash_hex(file):
    _hash = sha1()
    with open(file, "rb") as f:
        for block in iter(lambda: f.read(BLOCK_SIZE_MB * 1024 * 1024), b""):
            _hash.update(block)

    return _hash.hexdigest()


@pytest.mark.e2e
def test_empty_directory_ls_output(run):
    _dir = f"e2e-{uuid()}"
    _path = f"/tmp/{_dir}"

    # Create directory for the test
    _, captured = run(["store", "mkdir", f"storage://{_path}"])
    assert not captured.err
    assert captured.out == f"storage://{_path}\n"

    # Ensure output of ls - empty directory shall print nothing.
    _, captured = run(["store", "ls", f"storage://{_path}"])
    assert not captured.err
    assert captured.out.isspace()

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
    _, captured = run(["store", "mkdir", f"storage://{_path}"])
    assert not captured.err
    assert captured.out == f"storage://{_path}\n"

    # Upload local file
    _, captured = run(["store", "cp", file, f"storage://{_path}/foo"])
    assert not captured.err
    assert (_path + "/foo") in captured.out

    # Confirm file has been uploaded
    _, captured = run(["store", "ls", f"storage://{_path}"])
    captured_output_list = captured.out.split("\n")
    expected_line = format_list(type="file", size=16777216, name="foo")
    assert expected_line in captured_output_list

    assert not captured.err

    # Download into local file and confirm checksum
    _local = join(tmpdir, "bar")
    _, captured = run(["store", "cp", f"storage://{_path}/foo", _local])
    assert hash_hex(_local) == checksum

    # Download into local dir and confirm checksum
    _local = join(tmpdir, "bardir")
    _local_file = join(_local, "foo")
    tmpdir.mkdir("bardir")
    _, captured = run(["store", "cp", f"storage://{_path}/foo", _local])
    assert hash_hex(_local_file) == checksum

    # Rename file on the storage
    _, captured = run(
        ["store", "mv", f"storage://{_path}/foo", f"storage://{_path}/bar"]
    )
    assert not captured.err
    assert (_path + "/bar") in captured.out

    # Confirm file has been renamed
    _, captured = run(["store", "ls", f"storage://{_path}"])
    captured_output_list = captured.out.split("\n")
    assert not captured.err
    expected_line = format_list(type="file", size=16777216, name="bar")
    assert expected_line in captured_output_list
    assert "foo" not in captured_output_list

    # Rename directory on the storage
    _dir2 = f"e2e-{uuid()}"
    _path2 = f"/tmp/{_dir2}"
    _, captured = run(["store", "mv", f"storage://{_path}", f"storage://{_path2}"])
    assert not captured.err
    assert _path not in captured.out
    assert _path2 in captured.out

    # Remove test dir
    _, captured = run(["store", "rm", f"storage://{_path2}"])
    assert not captured.err

    # And confirm
    _, captured = run(["store", "ls", f"storage:///tmp"])

    split = captured.out.split("\n")
    assert format_list(name=_dir, size=0, type="directory") not in split

    assert not captured.err
