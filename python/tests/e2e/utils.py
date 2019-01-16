import re
from os.path import join
from time import sleep

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


def check_file_exists_on_storage(run, name: str, path: str, size: int):
    """
    Tests if file with given name and size exists in given path
    Assert if file absent or something went bad

    :param run: Runtime environment
    :param name: File name
    :param path: Path on storage
    :param size: File size
    :return:
    """
    delay = 5
    for i in range(5):
        try:
            captured = run(["store", "ls", f"storage://{path}"])
        except SystemExit:
            sleep(delay)
            delay *= 2
        captured_output_list = captured.out.split("\n")
        expected_line = format_list(type="file", size=size, name=name)
        assert not captured.err
        assert expected_line in captured_output_list
    raise AssertionError(f"Cannot find {name} in {path}")


def check_dir_exists_on_storage(run, name: str, path: str):
    """
    Tests if dir exists in given path
    Assert if dir absent or something went bad

    :param run: Runtime environment
    :param name: Directory name
    :param path: Path on storage
    :return:
    """
    captured = run(["store", "ls", f"storage://{path}"])
    captured_output_list = captured.out.split("\n")
    assert f"directory      0              {name}" in captured_output_list
    assert not captured.err


def check_dir_absent_on_storage(run, name: str, path: str):
    """
    Tests if dir with given name absent in given path.
    Assert if dir present or something went bad

    :param run: Runtime environment
    :param name: Dir name
    :param path: Path on storage
    :return:
    """
    captured = run(["store", "ls", f"storage://{path}"])
    split = captured.out.split("\n")
    assert format_list(name=name, size=0, type="directory") not in split
    assert not captured.err


def check_file_absent_on_storage(run, name: str, path: str):
    """
    Tests if file with given name absent in given path.
    Assert if file present or something went bad
    :param run: Runtime environment
    :param name: File name
    :param path: Path on storage
    :return:
    """
    captured = run(["store", "ls", f"storage://{path}"])
    pattern = format_list_pattern(name=name)
    assert not re.search(pattern, captured.out)
    assert not captured.err


def check_file_on_storage_checksum(
    run, name: str, path: str, checksum: str, tmpdir: str, tmpname: str
):
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
    _local = join(tmpdir, tmpname)
    run(["store", "cp", f"storage://{path}/{name}", _local])
    assert hash_hex(_local) == checksum


def check_create_dir_on_storage(run, path: str):
    """
    Create dir on storage and assert if something went bad
    :param run: Runtime environment
    :param path: Path on storage
    :return:
    """
    captured = run(["store", "mkdir", f"storage://{path}"])
    assert not captured.err
    assert captured.out == ""


def check_rmdir_on_storage(run, path: str):
    """
    Remove dir on storage and assert if something went bad
    :param run: Runtime environment
    :param path: Path on storage
    :return:
    """
    captured = run(["store", "rm", f"storage://{path}"])
    assert not captured.err


def check_rm_file_on_storage(run, name: str, path: str):
    """
    Remove file in given path in storage and if something went bad
    :param run: Runtime environment
    :param name: File name
    :param path: Path on storage
    :return:
    """
    captured = run(["store", "rm", f"storage://{path}/{name}"])
    assert not captured.err


def check_upload_file_to_storage(run, name: str, path: str, local_file: str):
    """
    Upload local file with given name to storage and assert if something went bad

    :param run: Runtime environment
    :param name: File name on storage, can be ommited
    :param path: Path on storage
    :param local_file: Local file name with path
    :return:
    """
    if name is None:
        captured = run(["store", "cp", local_file, f"storage://{path}"])
        assert not captured.err
        assert captured.out == ""

    else:
        captured = run(["store", "cp", local_file, f"storage://{path}/{name}"])
        assert not captured.err
        assert captured.out == ""


def check_rename_file_on_storage(
    run, name_from: str, path_from: str, name_to: str, path_to: str
):
    """
    Rename file on storage and assert if something went bad
    :param run: Runtime environment
    :param name_from: Source file name
    :param path_from: Source path
    :param name_to: Destination file name
    :param path_to: Destination path
    :return:
    """
    captured = run(
        [
            "store",
            "mv",
            f"storage://{path_from}/{name_from}",
            f"storage://{path_to}/{name_to}",
        ]
    )
    assert not captured.err
    assert captured.out == ""


def check_rename_directory_on_storage(run, path_from: str, path_to: str):
    """
    Rename directory on storage and assert if something went bad

    :param run:
    :param path_from:
    :param path_to:
    :return:
    """
    captured = run(["store", "mv", f"storage://{path_from}", f"storage://{path_to}"])
    assert not captured.err
    assert captured.out == ""
