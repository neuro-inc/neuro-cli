import os
import re
from os.path import join
from time import sleep

from _sha1 import sha1


BLOCK_SIZE_MB = 16
FILE_COUNT = 1
FILE_SIZE_MB = 16
GENERATION_TIMEOUT_SEC = 120
RC_TEXT = "url: http://platform.dev.neuromation.io/api/v1\nauth: {token}"
UBUNTU_IMAGE_NAME = "ubuntu:latest"
format_list = "{type:<15}{size:<15,}{name:<}".format
format_list_pattern = "(file|directory)\s*\d+\s*{name}".format
FS_SYNC_TIME = int(os.environ.get("CLIENT_TEST_E2E_FS_SYNC_TIME", 20))


def hash_hex(file):
    _hash = sha1()
    with open(file, "rb") as f:
        for block in iter(lambda: f.read(BLOCK_SIZE_MB * 1024 * 1024), b""):
            _hash.update(block)

    return _hash.hexdigest()


def fs_sync(periods: float = 1.0):
    """
    Just wait given count of time periods for FS sync
    :param periods:
    :return:
    """
    sleep(periods * FS_SYNC_TIME)


def attempt(attempts: int = 4, periods: float = 1.0):
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
                    fs_sync(periods)
                else:
                    return func(*args, **kwargs)

        return wrapped

    return _attempt


@attempt()
def check_file_exists_on_storage(run, name: str, path: str, size: int):
    _, captured = run(["store", "ls", f"storage://{path}"])
    captured_output_list = captured.out.split("\n")
    expected_line = format_list(type="file", size=size, name=name)
    assert expected_line in captured_output_list
    assert not captured.err


@attempt()
def check_dir_exists_on_storage(run, name: str, path: str):
    _, captured = run(["store", "ls", f"storage://{path}"])
    captured_output_list = captured.out.split("\n")
    assert f"directory      0              {name}" in captured_output_list
    assert not captured.err


@attempt()
def check_dir_absent_on_storage(run, name: str, path: str):
    _, captured = run(["store", "ls", f"storage://{path}"])
    split = captured.out.split("\n")
    assert format_list(name=name, size=0, type="directory") not in split
    assert not captured.err


@attempt()
def check_file_absent_on_storage(run, name: str, path: str):
    _, captured = run(["store", "ls", f"storage://{path}"])
    pattern = format_list_pattern(name=name)
    assert not re.search(pattern, captured.out)
    assert not captured.err


@attempt()
def check_file_on_storage_checksum(
    run, name: str, path: str, checksum: str, tmpdir: str, tmpname: str
):
    _local = join(tmpdir, tmpname)
    _, captured = run(["store", "cp", f"storage://{path}/{name}", _local])
    assert hash_hex(_local) == checksum


def check_create_dir_on_storage(run, path: str):
    _, captured = run(["store", "mkdir", f"storage://{path}"])
    assert not captured.err
    assert captured.out == f"storage://{path}\n"


@attempt()
def check_rmdir_on_storage(run, path: str):
    _, captured = run(["store", "rm", f"storage://{path}"])
    assert not captured.err


@attempt()
def check_rm_file_on_storage(run, name: str, path: str):
    _, captured = run(["store", "rm", f"storage://{path}/{name}"])
    assert not captured.err


def check_upload_file_to_storage(run, name: str, path: str, local_file: str):
    if name is None:
        _, captured = run(["store", "cp", local_file, f"storage://{path}"])
        assert not captured.err
        assert f"{path}" in captured.out

    else:
        _, captured = run(["store", "cp", local_file, f"storage://{path}/{name}"])
        assert not captured.err
        assert f"{path}/{name}" in captured.out


@attempt()
def check_rename_file_on_storage(
    run, name_from: str, path_from: str, name_to: str, path_to: str
):
    _, captured = run(
        [
            "store",
            "mv",
            f"storage://{path_from}/{name_from}",
            f"storage://{path_to}/{name_to}",
        ]
    )
    assert not captured.err
    assert f"{path_to}/{name_to}" in captured.out


@attempt()
def check_rename_directory_on_storage(run, path_from: str, path_to: str):
    _, captured = run(["store", "mv", f"storage://{path_from}", f"storage://{path_to}"])
    assert not captured.err
    assert path_from not in captured.out
    assert path_to in captured.out
