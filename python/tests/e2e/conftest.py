import asyncio
import os
import platform
import sys
from math import ceil
from os.path import join
from pathlib import Path
from uuid import uuid4 as uuid

import pytest

from tests.e2e.utils import (
    BLOCK_SIZE_MB,
    FILE_COUNT,
    FILE_SIZE_MB,
    GENERATION_TIMEOUT_SEC,
    RC_TEXT,
)


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
    e2e_test_token = os.environ["CLIENT_TEST_E2E_USER_NAME"]

    rc_text = RC_TEXT.format(token=e2e_test_token)
    tmpdir.join(".nmrc").open("w").write(rc_text)

    def _home():
        return Path(tmpdir)

    def _run(arguments):
        monkeypatch.setattr(Path, "home", _home)
        monkeypatch.setattr(sys, "argv", ["nmc"] + arguments)

        from neuromation.cli import main

        for i in range(5):
            try:
                main()
            except SystemExit as exc:
                if exc.code == os.EX_IOERR:
                    continue
                else:
                    pytest.fail(f"[{exc.code}] status code returned")
            return capsys.readouterr()

    return _run


@pytest.fixture
def remote_and_local(run):
    _dir = f"e2e-{uuid()}"
    _path = f"/tmp/{_dir}"

    captured = run(["store", "mkdir", f"storage://{_path}"])
    assert not captured.err
    assert captured.out == f"storage://{_path}" + "\n"

    return _path, _dir


@pytest.fixture(scope="session")
def nested_data(tmpdir_factory):
    loop = asyncio.get_event_loop()
    root_tmp_dir = tmpdir_factory.mktemp("data")
    tmp_dir = root_tmp_dir.mkdir("nested").mkdir("directory").mkdir("for").mkdir("test")
    data = loop.run_until_complete(
        generate_test_data(tmp_dir, FILE_COUNT, FILE_SIZE_MB)
    )
    return data[0][0], data[0][1], root_tmp_dir.strpath
