import re
from os.path import join
from time import sleep

import pytest

from _sha1 import sha1


BLOCK_SIZE_MB = 16
FILE_COUNT = 1
FILE_SIZE_MB = 16
GENERATION_TIMEOUT_SEC = 120
RC_TEXT = "url: https://platform.dev.neuromation.io/api/v1\nauth: {token}"
UBUNTU_IMAGE_NAME = "ubuntu:latest"
format_list = "{type:<15}{size:<15,}{name:<}".format
format_list_pattern = "(file|directory)\\s*\\d+\\s*{name}".format


def hash_hex(file):
    _hash = sha1()
    with open(file, "rb") as f:
        for block in iter(lambda: f.read(BLOCK_SIZE_MB * 1024 * 1024), b""):
            _hash.update(block)

    return _hash.hexdigest()


def attempt(attempts: int = 4, sleep_time: float = 15.0):
    """
    This decorator allow function fail up to _attempts_ times with
    pause _sleep_timeout_ seconds between each attempt
    :param attempts:
    :param sleep_time:
    :return:
    """

    def _attempt(func, *args, **kwargs):
        def wrapped(*args, **kwargs):
            nonlocal attempts
            while True:
                attempts -= 1
                if attempts > 0:
                    try:
                        return func(*args, **kwargs)
                    except BaseException:
                        pass
                    sleep(sleep_time)
                else:
                    return func(*args, **kwargs)

        return wrapped

    return _attempt


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
