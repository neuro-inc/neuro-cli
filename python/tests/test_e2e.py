import asyncio
import platform
from hashlib import sha1
from math import ceil
from os.path import join
from uuid import uuid4 as uuid

import pytest

BLOCK_SIZE_MB = 16
FILE_COUNT = 1
FILE_SIZE_MB = 16
GENERATION_TIMEOUT_SEC = 120
RC_TEXT = """
    url: http://platform.dev.neuromation.io/api/v1
"""

format_list = '{name:<20}{size:,}'.format


async def generate_test_data(root, count, size_mb):
    async def generate_file(name):
        exec_sha_name = 'sha1sum' if platform.platform() == "linux" else 'shasum'
        process = await asyncio.create_subprocess_shell(
                    f"""(dd if=/dev/urandom \
                    bs={BLOCK_SIZE_MB * 1024 * 1024} \
                    count={ceil(size_mb / BLOCK_SIZE_MB)} \
                    2>/dev/null) | \
                    tee {name} | \
                    {exec_sha_name}""",
                    stdout=asyncio.subprocess.PIPE)

        stdout, _ = await asyncio.wait_for(
            process.communicate(),
            timeout=GENERATION_TIMEOUT_SEC)

        # sha1sum appends file name to the output
        return name, stdout.decode()[:40]

    return await asyncio.gather(
        *[
            generate_file(join(root, name))
            for name in (
                str(uuid()) for _ in range(count))
        ])


@pytest.fixture(scope="session")
def data(tmpdir_factory):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        generate_test_data(
            tmpdir_factory.mktemp("data"),
            FILE_COUNT,
            FILE_SIZE_MB))


@pytest.fixture
def run(monkeypatch, capsys, tmpdir):
    import sys
    from pathlib import Path

    tmpdir.join('.nmrc').open('w').write(RC_TEXT)

    def _home():
        return Path(tmpdir)

    def _run(arguments):
        monkeypatch.setattr(
            Path, 'home', _home)
        monkeypatch.setattr(
            sys, 'argv',
            ['nmc'] + arguments)

        from neuromation.cli import main

        return main(), capsys.readouterr()

    return _run


def hash_hex(file):
    _hash = sha1()
    with open(file, "rb") as f:
        for block in iter(lambda: f.read(BLOCK_SIZE_MB * 1024 * 1024), b''):
            _hash.update(block)

    return _hash.hexdigest()


@pytest.mark.e2e
def test_e2e(data, run, tmpdir):
    file, checksum = data[0]

    _dir = f'e2e-{uuid()}'
    _path = f'/tmp/{_dir}'

    # Create directory for the test
    _, captured = run(['store', 'mkdir', _path])
    assert not captured.err
    assert captured.out == _path + '\n'

    # Upload local file
    _, captured = run([
            'store', 'cp', file, 'storage://' + _path + '/foo'
        ])
    assert not captured.err
    assert captured.out == 'storage://' + _path + '/foo' + '\n'

    # Confirm file has been uploaded
    _, captured = run(['store', 'ls', _path])
    captured_output_list = captured.out.split('\n')
    assert 'None' \
        not in captured_output_list
    assert format_list(name="foo", size=FILE_SIZE_MB * 1024 * 1024) \
        in captured_output_list
    assert not captured.err

    # Download into local file and confirm checksum
    _local = join(tmpdir, 'bar')
    _, captured = run([
        'store', 'cp',
        'storage://' + _path + '/foo', _local
    ])
    assert hash_hex(_local) == checksum

    # Remove test dir
    _, captured = run([
            'store', 'rm', _path
        ])
    assert not captured.err

    # And confirm
    _, captured = run([
            'store', 'ls', '/tmp'
        ])
    assert format_list(name=_dir, size=0) not in captured.out.split('\n')
    assert not captured.err
