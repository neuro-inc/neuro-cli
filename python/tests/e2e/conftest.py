import asyncio
import hashlib
import logging
import os
import re
from collections import namedtuple
from contextlib import suppress
from hashlib import sha1
from os.path import join
from pathlib import Path
from time import sleep, time
from uuid import uuid4 as uuid

import pytest
from yarl import URL

from neuromation.cli import main, rc
from neuromation.cli.command_progress_report import ProgressBase
from neuromation.client import FileStatusType
from neuromation.utils import run
from tests.e2e.utils import FILE_SIZE_B, RC_TEXT


JOB_TIMEOUT = 60 * 5
JOB_WAIT_SLEEP_SECONDS = 2


DUMMY_PROGRESS = ProgressBase.create_progress(False)

log = logging.getLogger(__name__)

job_id_pattern = re.compile(
    # pattern for UUID v4 taken here: https://stackoverflow.com/a/38191078
    r"(job-[0-9a-f]{8}-[0-9a-f]{4}-[4][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})",
    re.IGNORECASE,
)


class TestRetriesExceeded(Exception):
    pass


SysCap = namedtuple("SysCap", "out err")


def run_async(coro):
    def wrapper(*args, **kwargs):
        return run(coro(*args, **kwargs))

    return wrapper


class Helper:
    def __init__(self, config):
        self._config = config
        self._tmpstorage = "storage:" + str(uuid()) + "/"
        self.mkdir("")

    def close(self):
        if self._tmpstorage is not None:
            with suppress(Exception):
                self.rm("")
            self._tmpstorage = None

    @property
    def tmpstorage(self):
        return self._tmpstorage

    @run_async
    async def mkdir(self, path):
        url = URL(self.tmpstorage + path)
        async with self._config.make_client() as client:
            await client.storage.mkdirs(url)

    @run_async
    async def rm(self, path):
        url = URL(self.tmpstorage + path)
        async with self._config.make_client() as client:
            await client.storage.rm(url)

    @run_async
    async def check_file_exists_on_storage(self, name: str, path: str, size: int):
        path = URL(self.tmpstorage + path)
        async with self._config.make_client() as client:
            files = await client.storage.ls(path)
            for file in files:
                if (
                    file.type == FileStatusType.FILE
                    and file.name == name
                    and file.size == size
                ):
                    break
            else:
                raise AssertionError(
                    f"File {name} with size {size} not found in {path}"
                )

    @run_async
    async def check_dir_exists_on_storage(self, name: str, path: str):
        path = URL(self.tmpstorage + path)
        async with self._config.make_client() as client:
            files = await client.storage.ls(path)
            for file in files:
                if file.type == FileStatusType.DIRECTORY and file.path == name:
                    break
            else:
                raise AssertionError(f"Dir {name} not found in {path}")

    @run_async
    async def check_dir_absent_on_storage(self, name: str, path: str):
        path = URL(self.tmpstorage + path)
        async with self._config.make_client() as client:
            files = await client.storage.ls(path)
            for file in files:
                if file.type == FileStatusType.DIRECTORY and file.path == name:
                    raise AssertionError(f"Dir {name} found in {path}")

    @run_async
    async def check_file_absent_on_storage(self, name: str, path: str):
        path = URL(self.tmpstorage + path)
        async with self._config.make_client() as client:
            files = await client.storage.ls(path)
            for file in files:
                if file.type == FileStatusType.FILE and file.path == name:
                    raise AssertionError(f"File {name} found in {path}")

    @run_async
    async def check_file_on_storage_checksum(
        self, name: str, path: str, checksum: str, tmpdir: str, tmpname: str
    ):
        path = URL(self.tmpstorage + path)
        async with self._config.make_client() as client:
            if tmpname:
                target = join(tmpdir, tmpname)
                target_file = target
            else:
                target = tmpdir
                target_file = join(tmpdir, name)
            delay = 5  # need a relative big initial delay to synchronize 16MB file
            for i in range(5):
                await client.storage.download_dir(
                    DUMMY_PROGRESS, f"{path}/{name}", target
                )
                try:
                    assert self.hash_hex(target_file) == checksum
                    return
                except AssertionError:
                    # the file was not synchronized between platform storage nodes
                    # need to try again
                    await asyncio.sleep(delay)
                    delay *= 2
            raise AssertionError("checksum test failed for {path}")

    @run_async
    async def check_create_dir_on_storage(self, path: str):
        path = URL(self.tmpstorage + path)
        async with self._config.make_client() as client:
            await client.storage.mkdirs(path)

    @run_async
    async def check_rmdir_on_storage(self, path: str):
        path = URL(self.tmpstorage + path)
        async with self._config.make_client() as client:
            await client.rmdir(path)

    @run_async
    async def check_rm_file_on_storage(self, name: str, path: str):
        path = URL(self.tmpstorage + path)
        async with self._config.make_client() as client:
            await client.storage.rm(f"{path}/{name}")

    @run_async
    async def check_upload_file_to_storage(self, name: str, path: str, local_file: str):
        path = URL(self.tmpstorage + path)
        async with self._config.make_client() as client:
            if name is None:
                await client.storage.upload_file(DUMMY_PROGRESS, local_file, path)
            else:
                await client.storage.upload_file(
                    DUMMY_PROGRESS, URL("file:" + local_file), URL(f"{path}/{name}")
                )

    @run_async
    async def check_rename_file_on_storage(
        self, name_from: str, path_from: str, name_to: str, path_to: str
    ):
        async with self._config.make_client() as client:
            await client.storage.mv(
                URL(f"{self.tmpstorage}{path_from}/{name_from}"),
                URL(f"{self.tmpstorage}{path_to}/{name_to}"),
            )
            files1 = await client.storage.ls(URL(f"{self.tmpstorage}{path_from}"))
            names1 = {f.name for f in files1}
            assert name_from not in names1

            files2 = await client.storage.ls(URL(f"{self.tmpstorage}{path_to}"))
            names2 = {f.name for f in files2}
            assert name_to in names2

    @run_async
    async def check_rename_directory_on_storage(self, path_from: str, path_to: str):
        async with self._config.make_client() as client:
            await client.storage.mv(
                URL(f"{self.tmpstorage}{path_from}"), URL(f"{self.tmpstorage}{path_to}")
            )

    def hash_hex(self, file):
        _hash = sha1()
        with open(file, "rb") as f:
            for block in iter(lambda: f.read(16 * 1024 * 1024), b""):
                _hash.update(block)

        return _hash.hexdigest()

    @run_async
    async def wait_job_change_state_from(self, job_id, wait_state, stop_state=None):
        start_time = time()
        async with self._config.make_client() as client:
            job = await client.jobs.status(job_id)
            while job.status == wait_state and (int(time() - start_time) < JOB_TIMEOUT):
                if stop_state == job.status:
                    raise AssertionError(f"failed running job {job_id}: {stop_state}")
                await asyncio.sleep(JOB_WAIT_SLEEP_SECONDS)
                job = await client.jobs.status(job_id)

    @run_async
    async def wait_job_change_state_to(self, job_id, target_state, stop_state=None):
        start_time = time()
        async with self._config.make_client() as client:
            job = await client.jobs.status(job_id)
            while target_state != job.status:
                if stop_state == job.status:
                    raise AssertionError(f"failed running job {job_id}: '{stop_state}'")
                if int(time() - start_time) > JOB_TIMEOUT:
                    raise AssertionError(
                        f"timeout exceeded, last output: '{job.status}'"
                    )
                await asyncio.sleep(JOB_WAIT_SLEEP_SECONDS)
                job = await client.jobs.status(job_id)

    @run_async
    async def assert_job_state(self, job_id, state):
        async with self._config.make_client() as client:
            job = await client.jobs.status(job_id)
            assert job.status == state


@pytest.fixture
def config(tmp_path, monkeypatch):
    e2e_test_token = os.environ.get("CLIENT_TEST_E2E_USER_NAME")
    if e2e_test_token:
        # setup config for CircleCI build,
        # use existing config file otherwise
        rc_text = RC_TEXT.format(token=e2e_test_token)
        config_path = tmp_path / ".nmrc"
        config_path.write_text(rc_text)
        config_path.chmod(0o600)

        def _home():
            return Path(tmp_path)

        monkeypatch.setattr(Path, "home", _home)

    config = rc.ConfigFactory.load()
    yield config


@pytest.fixture
def helper(config):
    ret = Helper(config)
    yield ret
    ret.close()


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
def run_cli(capfd, config):
    executed_jobs_list = []

    def _run(arguments, *, storage_retry=True):
        log.info("Run 'neuro %s'", " ".join(arguments))

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
