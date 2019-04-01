import asyncio
import hashlib
import logging
import os
import re
import sys
from collections import namedtuple
from contextlib import suppress
from hashlib import sha1
from os.path import join
from pathlib import Path
from time import sleep, time
from typing import List, Optional
from uuid import uuid4 as uuid

import aiohttp
import pytest
from yarl import URL

from neuromation.cli import main, rc
from neuromation.cli.command_progress_report import ProgressBase
from neuromation.cli.const import EX_IOERR, EX_OK, EX_OSFILE
from neuromation.cli.rc import ENV_NAME as CFG_ENV_NAME
from neuromation.client import (
    FileStatusType,
    JobDescription,
    JobStatus,
    ResourceNotFound,
)
from neuromation.utils import run
from tests.e2e.utils import (
    FILE_SIZE_B,
    JOB_TINY_CONTAINER_PARAMS,
    NGINX_IMAGE_NAME,
    RC_TEXT,
    JobWaitStateStopReached,
)


JOB_TIMEOUT = 60 * 5
JOB_WAIT_SLEEP_SECONDS = 2
JOB_OUTPUT_TIMEOUT = 60 * 5
JOB_OUTPUT_SLEEP_SECONDS = 2
STORAGE_MAX_WAIT = 60
NETWORK_TIMEOUT = 60.0 * 3

DUMMY_PROGRESS = ProgressBase.create_progress(False)

log = logging.getLogger(__name__)

job_id_pattern = re.compile(
    # pattern for UUID v4 taken here: https://stackoverflow.com/a/38191078
    r"(job-[0-9a-f]{8}-[0-9a-f]{4}-[4][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})",
    re.IGNORECASE,
)


@pytest.fixture
def loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()


class TestRetriesExceeded(Exception):
    pass


SysCap = namedtuple("SysCap", "out err")


async def _run_async(coro, *args, **kwargs):
    try:
        return await coro(*args, **kwargs)
    finally:
        if sys.platform == "win32":
            await asyncio.sleep(0.2)
        else:
            await asyncio.sleep(0.05)


def run_async(coro):
    def wrapper(*args, **kwargs):
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        return run(_run_async(coro, *args, **kwargs))

    return wrapper


class Helper:
    def __init__(self, config: rc.Config, nmrc_path, capfd, tmp_path: Path):
        self._config = config
        self._nmrc_path = nmrc_path
        self._capfd = capfd
        self._tmp = tmp_path
        self._tmpstorage = "storage:" + str(uuid()) + "/"
        self._executed_jobs = []
        self.mkdir("")

    def close(self):
        if self._tmpstorage is not None:
            with suppress(Exception):
                self.rm("")
            self._tmpstorage = None
        if self._executed_jobs:
            with suppress(Exception):
                with suppress(Exception):
                    self.run_cli(["job", "kill"] + self._executed_jobs)

    @property
    def config(self):
        return self._config

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
        loop = asyncio.get_event_loop()
        t0 = loop.time()
        async with self._config.make_client() as client:
            while loop.time() - t0 < STORAGE_MAX_WAIT:
                try:
                    files = await client.storage.ls(path)
                except ResourceNotFound:
                    await asyncio.sleep(1)
                    continue
                for file in files:
                    if (
                        file.type == FileStatusType.FILE
                        and file.name == name
                        and file.size == size
                    ):
                        return
                await asyncio.sleep(1)
        raise AssertionError(f"File {name} with size {size} not found in {path}")

    @run_async
    async def check_dir_exists_on_storage(self, name: str, path: str):
        path = URL(self.tmpstorage + path)
        loop = asyncio.get_event_loop()
        t0 = loop.time()
        async with self._config.make_client() as client:
            while loop.time() - t0 < STORAGE_MAX_WAIT:
                try:
                    files = await client.storage.ls(path)
                except ResourceNotFound:
                    await asyncio.sleep(1)
                    continue
                for file in files:
                    if file.type == FileStatusType.DIRECTORY and file.path == name:
                        return
                await asyncio.sleep(1)
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
        if tmpname:
            target = join(tmpdir, tmpname)
            target_file = target
        else:
            target = tmpdir
            target_file = join(tmpdir, name)
        async with self._config.make_client() as client:
            delay = 5  # need a relative big initial delay to synchronize 16MB file
            await asyncio.sleep(delay)
            for i in range(5):
                try:
                    await client.storage.download_file(
                        DUMMY_PROGRESS, path / name, URL("file:" + target)
                    )
                except ResourceNotFound:
                    # the file was not synchronized between platform storage nodes
                    # need to try again
                    await asyncio.sleep(delay)
                    delay *= 2
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
            await client.storage.rm(path)

    @run_async
    async def check_rm_file_on_storage(self, name: str, path: str):
        path = URL(self.tmpstorage + path)
        delay = 0.5
        async with self._config.make_client() as client:
            for i in range(10):
                try:
                    await client.storage.rm(path / name)
                except ResourceNotFound:
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    return

    @run_async
    async def check_upload_file_to_storage(self, name: str, path: str, local_file: str):
        path = URL(self.tmpstorage + path)
        async with self._config.make_client() as client:
            if name is None:
                await client.storage.upload_file(
                    DUMMY_PROGRESS, URL("file:" + local_file), path
                )
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
                    raise JobWaitStateStopReached(
                        f"failed running job {job_id}: {stop_state}"
                    )
                await asyncio.sleep(JOB_WAIT_SLEEP_SECONDS)
                job = await client.jobs.status(job_id)

    @run_async
    async def wait_job_change_state_to(self, job_id, target_state, stop_state=None):
        start_time = time()
        async with self._config.make_client() as client:
            job = await client.jobs.status(job_id)
            while target_state != job.status:
                if stop_state == job.status:
                    raise JobWaitStateStopReached(
                        f"failed running job {job_id}: '{stop_state}'"
                    )
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

    @run_async
    async def job_info(self, job_id) -> JobDescription:
        async with self._config.make_client() as client:
            return await client.jobs.status(job_id)

    @run_async
    async def check_job_output(self, job_id, expected, flags=0):
        """
            Wait until job output satisfies given regexp
        """

        async def _check_job_output():
            async with self._config.make_client() as client:
                async for chunk in client.jobs.monitor(job_id):
                    yield chunk

        started_at = time()
        while time() - started_at < JOB_OUTPUT_TIMEOUT:
            chunks = []
            async for chunk in _check_job_output():
                if not chunk:
                    break
                chunks.append(chunk.decode())
                if re.search(expected, "".join(chunks), flags):
                    return
                if time() - started_at < JOB_OUTPUT_TIMEOUT:
                    break
                await asyncio.sleep(JOB_OUTPUT_SLEEP_SECONDS)

        raise AssertionError(
            f"Output of job {job_id} does not satisfy to expected regexp: {expected}"
        )

    def run_cli(self, arguments: List[str], storage_retry: bool = True) -> SysCap:

        log.info("Run 'neuro %s'", " ".join(arguments))

        delay = 0.5
        for i in range(5):
            pre_out, pre_err = self._capfd.readouterr()
            pre_out_size = len(pre_out)
            pre_err_size = len(pre_err)
            stored_nmrc_path = rc.ConfigFactory.get_path()
            try:
                rc.ConfigFactory.set_path(self._nmrc_path)
                main(
                    [
                        "--show-traceback",
                        "--disable-pypi-version-check",
                        "--color=no",
                        f"--network-timeout={self.config.network_timeout}",
                    ]
                    + arguments
                )
            except SystemExit as exc:
                if exc.code == EX_IOERR:
                    # network problem
                    sleep(delay)
                    delay *= 2
                    continue
                elif (
                    exc.code == EX_OSFILE
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
                elif exc.code != EX_OK:
                    raise
            finally:
                rc.ConfigFactory.set_path(stored_nmrc_path)
            post_out, post_err = self._capfd.readouterr()
            out = post_out[pre_out_size:]
            err = post_err[pre_err_size:]
            if any(
                " ".join(arguments).startswith(start)
                for start in ("submit", "job submit", "model train")
            ):
                match = job_id_pattern.search(out)
                if match:
                    self._executed_jobs.append(match.group(1))

            return SysCap(out.strip(), err.strip())
        else:
            raise TestRetriesExceeded(
                f"Retries exceeded during 'neuro {' '.join(arguments)}'"
            )

    def run_job(self, image, command="", params=[]) -> str:
        captured = self.run_cli(
            ["job", "submit", "-q"]
            + params
            + ([image, command] if command else [image])
        )
        assert not captured.err
        return captured.out

    def run_job_and_wait_state(
        self,
        image,
        command="",
        params=[],
        wait_state=JobStatus.RUNNING,
        stop_state=JobStatus.FAILED,
    ):
        job_id = self.run_job(image, command, params)
        assert job_id
        self.wait_job_change_state_from(job_id, JobStatus.PENDING, JobStatus.FAILED)
        self.wait_job_change_state_to(job_id, wait_state, stop_state)
        return job_id

    @run_async
    async def check_http_get(self, url):
        """
            Try to fetch given url few times.
        """
        async with aiohttp.ClientSession() as session:
            for i in range(3):
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.text()
                await asyncio.sleep(5)
            else:
                raise aiohttp.ClientResponseError(
                    status=resp.status,
                    message=f"Server return {resp.status}",
                    history=tuple(),
                    request_info=resp.request_info,
                )


@pytest.fixture()
def nmrc_path(tmp_path, monkeypatch):
    e2e_test_token = os.environ.get("CLIENT_TEST_E2E_USER_NAME")
    if e2e_test_token:
        nmrc_path = tmp_path / "conftest.nmrc"
        monkeypatch.setenv(CFG_ENV_NAME, str(nmrc_path))
        rc.ConfigFactory.set_path(nmrc_path)
    else:
        nmrc_path = rc.ConfigFactory.get_path()
    return nmrc_path


@pytest.fixture
def config(nmrc_path, monkeypatch):
    e2e_test_token = os.environ.get("CLIENT_TEST_E2E_USER_NAME")

    if e2e_test_token:
        rc_text = RC_TEXT.format(token=e2e_test_token)
        nmrc_path.write_text(rc_text)
        nmrc_path.chmod(0o600)

    config.network_timeout = NETWORK_TIMEOUT
    config = rc.ConfigFactory.load()
    yield config


@pytest.fixture
def helper(config, capfd, monkeypatch, tmp_path, nmrc_path):
    ret = Helper(config=config, nmrc_path=nmrc_path, capfd=capfd, tmp_path=tmp_path)
    yield ret
    ret.close()


@pytest.fixture()
def nmrc_path_alt(tmp_path, monkeypatch):
    e2e_test_token = os.environ.get("CLIENT_TEST_E2E_USER_NAME_ALT")
    if not e2e_test_token:
        pytest.skip("CLIENT_TEST_E2E_USER_NAME_ALT variable is not set")
    nmrc_path = tmp_path / "conftest-alt.nmrc"
    monkeypatch.setenv(CFG_ENV_NAME, str(nmrc_path))
    rc.ConfigFactory.set_path(nmrc_path)
    return nmrc_path


@pytest.fixture
def config_alt(tmp_path, nmrc_path_alt):
    e2e_test_token = os.environ.get("CLIENT_TEST_E2E_USER_NAME_ALT")
    if e2e_test_token:
        rc_text = RC_TEXT.format(token=e2e_test_token)
        nmrc_path_alt.write_text(rc_text)
        nmrc_path_alt.chmod(0o600)
    else:
        pytest.skip("CLIENT_TEST_E2E_USER_NAME_ALT variable is not set")

    config = rc.ConfigFactory.load()

    config.network_timeout = NETWORK_TIMEOUT
    yield config


@pytest.fixture
def helper_alt(config_alt, nmrc_path_alt, capfd, tmp_path):
    ret = Helper(
        config=config_alt, nmrc_path=nmrc_path_alt, capfd=capfd, tmp_path=tmp_path
    )
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
def secret_job(helper):
    def go(http_port: bool, http_auth: bool = False, description: Optional[str] = None):
        secret = str(uuid())
        # Run http job
        command = (
            f"bash -c \"echo -n '{secret}' > /usr/share/nginx/html/secret.txt; "
            f"timeout 15m /usr/sbin/nginx -g 'daemon off;'\""
        )
        args = []
        if http_port:
            args += ["--http", "80"]
            if http_auth:
                args += ["--http-auth"]
            else:
                args += ["--no-http-auth"]
        if not description:
            description = "nginx with secret file"
            if http_port:
                description += " and forwarded http port"
                if http_auth:
                    description += " with authentication"
        args += ["-d", description]
        http_job_id = helper.run_job_and_wait_state(
            NGINX_IMAGE_NAME, command, JOB_TINY_CONTAINER_PARAMS + args
        )
        status: JobDescription = helper.job_info(http_job_id)
        return {
            "id": http_job_id,
            "secret": secret,
            "ingress_url": status.http_url,
            "internal_hostname": status.internal_hostname,
        }

    return go
