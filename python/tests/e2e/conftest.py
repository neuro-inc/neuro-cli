import asyncio
import logging
import os
import platform
import re
import sys
from collections import namedtuple
from math import ceil
from os.path import join
from pathlib import Path
from time import sleep
from uuid import uuid4 as uuid

import pytest

from neuromation.cli import main
from tests.e2e.utils import (
    BLOCK_SIZE_MB,
    FILE_COUNT,
    FILE_SIZE_MB,
    GENERATION_TIMEOUT_SEC,
    RC_TEXT,
    format_list,
    format_list_pattern,
    hash_hex,
)


log = logging.getLogger(__name__)

job_id_pattern = r"Job ID:\s*(\S+)"


SysCap = namedtuple("SysCap", "out err")


@pytest.fixture
def tmpstorage(run, request):
    url = "storage:" + str(uuid()) + "/"
    captured = run(["storage", "mkdir", url])
    assert not captured.err
    assert captured.out == ""

    yield url
    # Remove directory only if test succeeded
    if not request.node._report_sections:  # TODO: find another way to check test status
        try:
            run(["storage", "rm", url])
        except BaseException:
            # Just ignore cleanup error here
            pass


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
            generate_file(str(root / name))
            for name in ("{:04d}.bin".format(i) for i in range(count))
        ]
    )


@pytest.fixture(scope="session")
def static_path(tmp_path_factory):
    return tmp_path_factory.mktemp("data")


@pytest.fixture(scope="session")
def data(static_path):
    loop = asyncio.get_event_loop()
    folder = static_path / "data"
    folder.mkdir()
    return loop.run_until_complete(generate_test_data(folder, FILE_COUNT, FILE_SIZE_MB))


@pytest.fixture(scope="session")
def nested_data(static_path):
    loop = asyncio.get_event_loop()
    root_dir = static_path / "neested_data" / "nested"
    nested_dir = root_dir / "directory" / "for" / "test"
    nested_dir.mkdir(parents=True, exist_ok=True)
    data = loop.run_until_complete(
        generate_test_data(nested_dir, FILE_COUNT, FILE_SIZE_MB)
    )
    return data[0][0], data[0][1], str(root_dir)


@pytest.fixture
def run(monkeypatch, capfd, tmp_path, setup_null_keyring):
    executed_jobs_list = []
    e2e_test_token = os.environ["CLIENT_TEST_E2E_USER_NAME"]

    rc_text = RC_TEXT.format(token=e2e_test_token)
    config_path = tmp_path / ".nmrc"
    config_path.write_text(rc_text)

    def _home():
        return Path(tmp_path)

    def _run(arguments, *, storage_retry=True):
        log.info("Run 'neuro %s'", " ".join(arguments))
        monkeypatch.setattr(Path, "home", _home)

        delay = 0.5
        for i in range(5):
            pre_out, pre_err = capfd.readouterr()
            pre_out_size = len(pre_out)
            pre_err_size = len(pre_err)
            try:
                main(["neuro"] + ["--show-traceback"] + arguments)
            except SystemExit as exc:
                if exc.code == os.EX_IOERR:
                    # network problem
                    sleep(delay)
                    delay *= 2
                    continue
                elif (
                    exc.code == os.EX_OSFILE
                    and arguments
                    and arguments[0] == "storage"
                    and storage_retry
                ):
                    # NFS storage has a lag between pushing data on one storage API node
                    # and fetching it on other node
                    # retry is the only way to avoid it
                    sleep(delay)
                    delay *= 2
                    continue
                elif exc.code != os.EX_OK:
                    raise
            post_out, post_err = capfd.readouterr()
            out = post_out[pre_out_size:]
            err = post_err[pre_err_size:]
            if arguments[0:2] in (["job", "submit"], ["model", "train"]):
                match = re.search(job_id_pattern, out)
                if match:
                    executed_jobs_list.append(match.group(1))

            return SysCap(out.strip(), err.strip())

    yield _run
    # try to kill all executed jobs regardless of the status
    if executed_jobs_list:
        try:
            _run(["job", "kill"] + executed_jobs_list)
        except BaseException:
            # Just ignore cleanup error here
            pass


@pytest.fixture
def check_file_exists_on_storage(run, tmpstorage):
    """
    Tests if file with given name and size exists in given path
    Assert if file absent or something went bad
    """

    def go(name: str, path: str, size: int):
        path = tmpstorage + path
        captured = run(["storage", "ls", path])
        captured_output_list = captured.out.split("\n")
        expected_line = format_list(type="file", size=size, name=name)
        assert not captured.err
        assert expected_line in captured_output_list

    return go


@pytest.fixture
def check_dir_exists_on_storage(run, tmpstorage):
    """
    Tests if dir exists in given path
    Assert if dir absent or something went bad
    """

    def go(name: str, path: str):
        path = tmpstorage + path
        captured = run(["storage", "ls", path])
        captured_output_list = captured.out.split("\n")
        assert f"directory      0              {name}" in captured_output_list
        assert not captured.err

    return go


@pytest.fixture
def check_dir_absent_on_storage(run, tmpstorage):
    """
    Tests if dir with given name absent in given path.
    Assert if dir present or something went bad
    """

    def go(name: str, path: str):
        path = tmpstorage + path
        captured = run(["storage", "ls", path])
        split = captured.out.split("\n")
        assert format_list(name=name, size=0, type="directory") not in split
        assert not captured.err

    return go


@pytest.fixture
def check_file_absent_on_storage(run, tmpstorage):
    """
    Tests if file with given name absent in given path.
    Assert if file present or something went bad
    """

    def go(name: str, path: str):
        path = tmpstorage + path
        captured = run(["storage", "ls", path])
        pattern = format_list_pattern(name=name)
        assert not re.search(pattern, captured.out)
        assert not captured.err

    return go


@pytest.fixture
def check_file_on_storage_checksum(run, tmpstorage):
    """
    Tests if file on storage in given path has same checksum. File will be downloaded
    to temporary folder first. Assert if checksum mismatched
    """

    def go(name: str, path: str, checksum: str, tmpdir: str, tmpname: str):
        path = tmpstorage + path
        if tmpname:
            target = join(tmpdir, tmpname)
            target_file = target
        else:
            target = tmpdir
            target_file = join(tmpdir, name)
        delay = 5  # need a relative big initial delay to synchronize 16MB file
        for i in range(5):
            run(["storage", "cp", f"{path}/{name}", target])
            try:
                assert hash_hex(target_file) == checksum
                return
            except AssertionError:
                # the file was not synchronized between platform storage nodes
                # need to try again
                sleep(delay)
                delay *= 2
        raise AssertionError("checksum test failed for {path}")

    return go


@pytest.fixture
def check_create_dir_on_storage(run, tmpstorage):
    """
    Create dir on storage and assert if something went bad
    """

    def go(path: str):
        path = tmpstorage + path
        captured = run(["storage", "mkdir", path])
        assert not captured.err
        assert captured.out == ""

    return go


@pytest.fixture
def check_rmdir_on_storage(run, tmpstorage):
    """
    Remove dir on storage and assert if something went bad
    """

    def go(path: str):
        path = tmpstorage + path
        captured = run(["storage", "rm", path])
        assert not captured.err

    return go


@pytest.fixture
def check_rm_file_on_storage(run, tmpstorage):
    """
    Remove file in given path in storage and if something went bad
    """

    def go(name: str, path: str):
        path = tmpstorage + path
        captured = run(["storage", "rm", f"{path}/{name}"])
        assert not captured.err

    return go


@pytest.fixture
def check_upload_file_to_storage(run, tmpstorage):
    """
    Upload local file with given name to storage and assert if something went bad
    """

    def go(name: str, path: str, local_file: str):
        path = tmpstorage + path
        if name is None:
            captured = run(["storage", "cp", local_file, f"{path}"])
            assert not captured.err
            assert captured.out == ""
        else:
            captured = run(["storage", "cp", local_file, f"{path}/{name}"])
            assert not captured.err
            assert captured.out == ""

    return go


@pytest.fixture
def check_rename_file_on_storage(run, tmpstorage):
    """
    Rename file on storage and assert if something went bad
    """

    def go(name_from: str, path_from: str, name_to: str, path_to: str):
        captured = run(
            [
                "storage",
                "mv",
                f"{tmpstorage}{path_from}/{name_from}",
                f"{tmpstorage}{path_to}/{name_to}",
            ]
        )
        assert not captured.err
        assert captured.out == ""

    return go


@pytest.fixture
def check_rename_directory_on_storage(run, tmpstorage):
    """
    Rename directory on storage and assert if something went bad
    """

    def go(path_from: str, path_to: str):
        captured = run(
            ["storage", "mv", f"{tmpstorage}{path_from}", f"{tmpstorage}{path_to}"]
        )
        assert not captured.err
        assert captured.out == ""

    return go
