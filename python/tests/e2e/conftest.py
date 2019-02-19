import hashlib
import logging
import os
import re
from collections import namedtuple
from os.path import join
from pathlib import Path
from shutil import move
from time import sleep
from uuid import uuid4 as uuid

import pytest

from neuromation.cli import main
from neuromation.client import FileStatusType
from neuromation.utils import run as run_async
from tests.e2e.utils import FILE_SIZE_B, RC_TEXT, attempt, hash_hex, output_to_files


log = logging.getLogger(__name__)

job_id_pattern = re.compile(
    # pattern for UUID v4 taken here: https://stackoverflow.com/a/38191078
    r"(job-[0-9a-f]{8}-[0-9a-f]{4}-[4][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})",
    re.IGNORECASE,
)


class TestRetriesExceeded(Exception):
    pass


SysCap = namedtuple("SysCap", "out err")


@pytest.fixture
def tmpstorage(run, request):
    url = "storage:" + str(uuid()) + "/"
    captured = run(["storage", "mkdir", url])
    assert not captured.err
    assert captured.out == ""

    yield url

    try:
        run(["storage", "rm", url])
    except BaseException:
        # Just ignore cleanup error here
        pass


def generate_random_file(path: Path, size):
    name = f"{uuid()}.tmp"
    path_and_name = path / name
    hasher = hashlib.sha1()
    with open(path_and_name, "wb") as file:
        generated = 0
        while generated < size:
            length = min(1024 * 1024, size - generated)
            data = os.urandom(length)
            file.write(data)
            hasher.update(data)
            generated += len(data)
    return str(path_and_name), hasher.hexdigest()


@pytest.fixture(scope="session")
def static_path(tmp_path_factory):
    return tmp_path_factory.mktemp("data")


@pytest.fixture(scope="session")
def data(static_path):
    folder = static_path / "data"
    folder.mkdir()
    return generate_random_file(folder, FILE_SIZE_B)


@pytest.fixture(scope="session")
def nested_data(static_path):
    root_dir = static_path / "neested_data" / "nested"
    nested_dir = root_dir / "directory" / "for" / "test"
    nested_dir.mkdir(parents=True, exist_ok=True)
    generated_file, hash = generate_random_file(nested_dir, FILE_SIZE_B)
    return generated_file, hash, str(root_dir)


@pytest.fixture
def run(monkeypatch, capfd, tmp_path):
    executed_jobs_list = []
    e2e_test_token = os.environ["CLIENT_TEST_E2E_USER_NAME"]

    rc_text = RC_TEXT.format(token=e2e_test_token)
    config_path = tmp_path / ".nmrc"
    config_path.write_text(rc_text)
    config_path.chmod(0o600)

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
                main(["--show-traceback", "--disable-pypi-version-check"] + arguments)
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
                match = job_id_pattern.search(out)
                if match:
                    executed_jobs_list.append(match.group(1))

            return SysCap(out.strip(), err.strip())
        else:
            raise TestRetriesExceeded(
                f"Retries exceeded during 'neuro {' '.join(arguments)}'"
            )

    yield _run
    # try to kill all executed jobs regardless of the status
    if executed_jobs_list:
        try:
            _run(["job", "kill"] + executed_jobs_list)
        except BaseException:
            # Just ignore cleanup error here
            pass


@pytest.fixture
def switch_user(tmp_path):
    """
        This fixture allow switch effective user for running `neuro`
        between CLIENT_TEST_E2E_USER_NAME and CLIENT_TEST_E2E_USER_NAME_ALT

        After test it will revert default user back
        But it can breaks e2e cleanup, please made cleanup for alt user self
    """
    switched: bool = False

    def _switch():
        nonlocal switched
        config_path = tmp_path / ".nmrc"
        backup_patch = tmp_path / ".nmrc.backup"
        if switched:
            move(backup_patch, config_path)
        else:
            move(config_path, backup_patch)
            e2e_test_token = os.environ["CLIENT_TEST_E2E_USER_NAME_ALT"]
            rc_text = RC_TEXT.format(token=e2e_test_token)
            config_path.write_text(rc_text)
            config_path.chmod(0o600)
        switched = not switched

    yield _switch

    if switched:
        _switch()


@pytest.fixture()
def check_job_output(run):
    """
        Wait while job output will satisfy given regexp
    """

    @attempt()
    def go(job_id, expected, flags=0):
        captured = run(["job", "logs", job_id])
        assert not captured.err
        assert re.search(expected, captured.out, flags)

    return go


@pytest.fixture
def check_file_exists_on_storage(run, tmpstorage):
    """
    Tests if file with given name and size exists in given path
    Assert if file absent or something went bad
    """

    def go(name: str, path: str, size: int):
        path = tmpstorage + path
        captured = run(["storage", "ls", "-l", path])
        assert not captured.err
        files = output_to_files(captured.out)
        for file in files:
            if (
                file.type == FileStatusType.FILE
                and file.name == name
                and file.size == size
            ):
                break
        else:
            raise AssertionError(f"File {name} with size {size} not found in {path}")

    return go


@pytest.fixture
def check_dir_exists_on_storage(run, tmpstorage):
    """
    Tests if dir exists in given path
    Assert if dir absent or something went bad
    """

    def go(name: str, path: str):
        path = tmpstorage + path
        captured = run(["storage", "ls", "-l", path])
        assert not captured.err
        files = output_to_files(captured.out)
        for file in files:
            if file.type == FileStatusType.DIRECTORY and file.path == name:
                break
        else:
            raise AssertionError(f"Dir {name} not found in {path}")

    return go


@pytest.fixture
def check_dir_absent_on_storage(run, tmpstorage):
    """
    Tests if dir with given name absent in given path.
    Assert if dir present or something went bad
    """

    def go(name: str, path: str):
        path = tmpstorage + path
        captured = run(["storage", "ls", "-l", path])
        assert not captured.err
        files = output_to_files(captured.out)
        for file in files:
            if file.type == FileStatusType.DIRECTORY and file.path == name:
                raise AssertionError(f"Dir {name} found in {path}")

    return go


@pytest.fixture
def check_file_absent_on_storage(run, tmpstorage):
    """
    Tests if file with given name absent in given path.
    Assert if file present or something went bad
    """

    def go(name: str, path: str):
        path = tmpstorage + path
        captured = run(["storage", "ls", "-l", path])
        assert not captured.err
        files = output_to_files(captured.out)
        for file in files:
            if file.type == FileStatusType.FILE and file.path == name:
                raise AssertionError(f"File {name} found in {path}")

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
