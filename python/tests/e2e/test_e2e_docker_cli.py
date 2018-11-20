import asyncio
import platform
import subprocess
from math import ceil
from os.path import join
from unittest import mock
from uuid import uuid4 as uuid

import pytest

from neuromation.cli.rc import ConfigFactory


BLOCK_SIZE_MB = 16
FILE_COUNT = 1
FILE_SIZE_MB = 16
GENERATION_TIMEOUT_SEC = 120
RC_TEXT = """url: http://platform.dev.neuromation.io/api/v1
auth: {token}"""

UBUNTU_IMAGE_NAME = "ubuntu:latest"

JWT_HDR = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
JWT_CLAIM = "eyJpZGVudGl0eSI6Im5ldXJvbWF0aW9uLWlzLWF3ZXNvbWUhIn0"
JWT_SIG = "5T0RGa9aWv_XVFHQKjlrJEZ_5S8kHkxmzIvj4tnBOis"

CUSTOM_TOKEN_FOR_TESTS = f"{JWT_HDR}.{JWT_CLAIM}.{JWT_SIG}"

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
def run(monkeypatch, capsys, tmpdir, setup_local_keyring):
    import sys
    from pathlib import Path

    rc_text = RC_TEXT.format(token=CUSTOM_TOKEN_FOR_TESTS)
    tmpdir.join(".nmrc").open("w").write(rc_text)

    def _home():
        return Path(tmpdir)

    def _run(arguments):
        monkeypatch.setattr(Path, "home", _home)
        monkeypatch.setattr(sys, "argv", ["nmc"] + arguments)

        from neuromation.cli import main

        return main(), capsys.readouterr()

    return _run


def test_docker_config_no_docker(run, monkeypatch):
    with mock.patch("subprocess.run") as runMock:
        runMock.side_effect = subprocess.CalledProcessError(
            returncode=2, cmd="no command"
        )
        _, captured = run(["config", "auth", CUSTOM_TOKEN_FOR_TESTS])
        assert runMock.call_count == 1

    assert CUSTOM_TOKEN_FOR_TESTS == ConfigFactory.load().auth


def test_docker_push_no_docker(run, monkeypatch):
    with mock.patch("subprocess.run") as runMock:
        runMock.side_effect = subprocess.CalledProcessError(
            returncode=2, cmd="no command"
        )
        with pytest.raises(OSError):
            _, captured = run(["image", "push", "abrakadabra"])
        assert runMock.call_count == 1


def test_docker_pull_no_docker(run, monkeypatch):
    with mock.patch("subprocess.run") as runMock:
        runMock.side_effect = subprocess.CalledProcessError(
            returncode=2, cmd="no command"
        )
        with pytest.raises(OSError):
            _, captured = run(["image", "pull", "abrakadabra"])
        assert runMock.call_count == 1


def test_docker_config_with_docker(run, monkeypatch):
    with mock.patch("subprocess.run") as runMock:
        _, captured = run(["config", "auth", CUSTOM_TOKEN_FOR_TESTS])
        assert runMock.call_count == 2

    assert CUSTOM_TOKEN_FOR_TESTS == ConfigFactory.load().auth


def test_docker_push_with_docker(run, monkeypatch):
    with mock.patch("subprocess.run") as runMock:
        _, captured = run(["image", "push", "abrakadabra"])
        assert runMock.call_count == 3


def test_docker_pull_with_docker(run, monkeypatch):
    with mock.patch("subprocess.run") as runMock:
        _, captured = run(["image", "pull", "abrakadabra"])
        assert runMock.call_count == 2
