import asyncio
import logging
import os
import platform
import re
import sys
from math import ceil
from os.path import join
from pathlib import Path
from time import sleep
from uuid import uuid4 as uuid

import pytest

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


@pytest.fixture(scope="session")
def tmpstorage():
    return "storage://" + uuid() + "/"


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


@pytest.fixture
def run(monkeypatch, capsys, tmpdir, setup_local_keyring):
    executed_jobs_list = []
    e2e_test_token = os.environ["CLIENT_TEST_E2E_USER_NAME"]

    rc_text = RC_TEXT.format(token=e2e_test_token)
    tmpdir.join(".nmrc").open("w").write(rc_text)

    def _home():
        return Path(tmpdir)

    def _run(arguments):
        log.info("Run 'neuro %s'", " ".join(arguments))
        monkeypatch.setattr(Path, "home", _home)
        monkeypatch.setattr(sys, "argv", ["nmc"] + arguments + ["--show-traceback"])

        from neuromation.cli import main

        for i in range(5):
            try:
                main()
            except SystemExit as exc:
                if exc.code == os.EX_IOERR:
                    continue
                else:
                    raise
            output = capsys.readouterr()
            if (
                "-v" not in arguments and "--version" not in arguments
            ):  # special case for version switch
                if arguments[0:2] in (["job", "submit"], ["model", "train"]):
                    match = re.search(job_id_pattern, output.out)
                    if match:
                        executed_jobs_list.append(match.group(1))

            return output

    yield _run
    # try to kill all executed jobs regardless of the status
    if executed_jobs_list:
        try:
            _run(["job", "kill"] + executed_jobs_list)
        except BaseException:
            # Just ignore cleanup error here
            pass


@pytest.fixture
def remote_and_local(run, request, tmpstorage):
    _dir = f"e2e-{uuid()}"
    _path = f"/tmp/{_dir}"

    captured = run(["store", "mkdir", f"{tmpstorage}{_path}"])
    assert not captured.err
    assert captured.out == ""

    yield _path, _dir
    # Remove directory only if test succeeded
    if not request.node._report_sections:  # TODO: find another way to check test status
        try:
            run(["store", "rm", f"{tmpstorage}{_path}"])
        except BaseException:
            # Just ignore cleanup error here
            pass


@pytest.fixture(scope="session")
def nested_data(tmpdir_factory):
    loop = asyncio.get_event_loop()
    root_tmp_dir = tmpdir_factory.mktemp("data")
    tmp_dir = root_tmp_dir.mkdir("nested").mkdir("directory").mkdir("for").mkdir("test")
    data = loop.run_until_complete(
        generate_test_data(tmp_dir, FILE_COUNT, FILE_SIZE_MB)
    )
    return data[0][0], data[0][1], root_tmp_dir.strpath


@pytest.fixture
def check_file_exists_on_storage(run, tmpstorage):
    """
    Tests if file with given name and size exists in given path
    Assert if file absent or something went bad

    :param run: Runtime environment
    :param name: File name
    :param path: Path on storage
    :param size: File size
    :return:
    """

    def go(name: str, path: str, size: int):
        delay = 5
        for i in range(5):
            try:
                captured = run(["store", "ls", f"{tmpstorage}{path}"])
            except SystemExit:
                sleep(delay)
                delay *= 2
            captured_output_list = captured.out.split("\n")
            expected_line = format_list(type="file", size=size, name=name)
            assert not captured.err
            assert expected_line in captured_output_list
            return
        else:
            raise AssertionError(f"Cannot find {name} in {path}")

    return go


@pytest.fixture
def check_dir_exists_on_storage(run, tmpstorage):
    """
    Tests if dir exists in given path
    Assert if dir absent or something went bad

    :param run: Runtime environment
    :param name: Directory name
    :param path: Path on storage
    :return:
    """

    def go(name: str, path: str):
        delay = 5
        for i in range(5):
            try:
                captured = run(["store", "ls", f"{tmpstorage}{path}"])
                captured_output_list = captured.out.split("\n")
                assert f"directory      0              {name}" in captured_output_list
                assert not captured.err
            except SystemExit:
                sleep(delay)
                delay *= 2
        else:
            raise AssertionError(f"Cannot check dir exist {name} on {path}")

    return go


@pytest.fixture
def check_dir_absent_on_storage(run, tmpstorage):
    """
    Tests if dir with given name absent in given path.
    Assert if dir present or something went bad

    :param run: Runtime environment
    :param name: Dir name
    :param path: Path on storage
    :return:
    """

    def go(name: str, path: str):
        delay = 5
        for i in range(5):
            try:
                captured = run(["store", "ls", f"{tmpstorage}{path}"])
                split = captured.out.split("\n")
                assert format_list(name=name, size=0, type="directory") not in split
                assert not captured.err
                return
            except SystemExit:
                sleep(delay)
                delay *= 2
        else:
            raise AssertionError(f"Cannot check absence dir {name} on {path}")

    return go


@pytest.fixture
def check_file_absent_on_storage(run, tmpstorage):
    """
    Tests if file with given name absent in given path.
    Assert if file present or something went bad
    :param run: Runtime environment
    :param name: File name
    :param path: Path on storage
    :return:
    """

    def go(name: str, path: str):
        delay = 5
        for i in range(5):
            try:
                captured = run(["store", "ls", f"{tmpstorage}{path}"])
                pattern = format_list_pattern(name=name)
                assert not re.search(pattern, captured.out)
                assert not captured.err
                return
            except SystemExit:
                sleep(delay)
                delay *= 2
        else:
            raise AssertionError(f"Cannot check absence file {name} on {path}")

    return go


@pytest.fixture
def check_file_on_storage_checksum(run, tmpstorage):
    """
    Tests if file on storage in given path has same checksum. File will be downloaded
    to temporary folder first. Assert if checksum mismatched
    :param run: Runtime environment
    :param name: File name
    :param path: Path on storage
    :param checksum: Checksum string
    :param tmpdir: Temporary dir
    :param tmpname:  Temporary name
    :return:
    """

    def go(name: str, path: str, checksum: str, tmpdir: str, tmpname: str):
        _local = join(tmpdir, tmpname)
        delay = 5
        for i in range(5):
            try:
                run(["store", "cp", f"{tmpstorage}{path}/{name}", _local])
                assert hash_hex(_local) == checksum
                return
            except SystemExit:
                sleep(delay)
                delay *= 2
        else:
            raise AssertionError(f"Cannot check sum {name} on {path}")

    return go


@pytest.fixture
def check_create_dir_on_storage(run, tmpstorage):
    """
    Create dir on storage and assert if something went bad
    :param run: Runtime environment
    :param path: Path on storage
    :return:
    """

    def go(path: str):
        delay = 5
        for i in range(5):
            try:
                captured = run(["store", "mkdir", f"{tmpstorage}{path}"])
                assert not captured.err
                assert captured.out == ""
                return
            except SystemExit:
                sleep(delay)
                delay *= 2
        else:
            raise AssertionError(f"Cannot create dir{path}")

    return go


@pytest.fixture
def check_rmdir_on_storage(run, tmpstorage):
    """
    Remove dir on storage and assert if something went bad
    :param run: Runtime environment
    :param path: Path on storage
    :return:
    """

    def go(path: str):
        delay = 5
        for i in range(5):
            try:
                captured = run(["store", "rm", f"{tmpstorage}{path}"])
                assert not captured.err
                return
            except SystemExit:
                sleep(delay)
                delay *= 2
        else:
            raise AssertionError(f"Cannot rmdir {path}")

    return go


@pytest.fixture
def check_rm_file_on_storage(run, tmpstorage):
    """
    Remove file in given path in storage and if something went bad
    :param run: Runtime environment
    :param name: File name
    :param path: Path on storage
    :return:
    """

    def go(name: str, path: str):
        delay = 5
        for i in range(5):
            try:
                captured = run(["store", "rm", f"{tmpstorage}{path}/{name}"])
                assert not captured.err
                return
            except SystemExit:
                sleep(delay)
                delay *= 2
        else:
            raise AssertionError(f"Cannot rm {name} on {path}")

    return go


@pytest.fixture
def check_upload_file_to_storage(run, tmpstorage):
    """
    Upload local file with given name to storage and assert if something went bad

    :param run: Runtime environment
    :param name: File name on storage, can be ommited
    :param path: Path on storage
    :param local_file: Local file name with path
    :return:
    """

    def go(name: str, path: str, local_file: str):
        if name is None:
            captured = run(["store", "cp", local_file, f"{tmpstorage}{path}"])
            assert not captured.err
            assert captured.out == ""
        else:
            captured = run(["store", "cp", local_file, f"{tmpstorage}{path}/{name}"])
            assert not captured.err
            assert captured.out == ""

    return go


@pytest.fixture
def check_rename_file_on_storage(run, tmpstorage):
    """
    Rename file on storage and assert if something went bad
    :param run: Runtime environment
    :param name_from: Source file name
    :param path_from: Source path
    :param name_to: Destination file name
    :param path_to: Destination path
    :return:
    """

    def go(name_from: str, path_from: str, name_to: str, path_to: str):
        captured = run(
            [
                "store",
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

    :param run:
    :param path_from:
    :param path_to:
    :return:
    """

    def go(path_from: str, path_to: str):
        captured = run(
            ["store", "mv", f"{tmpstorage}{path_from}", f"{tmpstorage}{path_to}"]
        )
        assert not captured.err
        assert captured.out == ""

    return go
