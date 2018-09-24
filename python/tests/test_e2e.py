import asyncio
import platform
import re
from hashlib import sha1
from math import ceil
from os.path import join
from time import sleep, time
from urllib.parse import urlparse
from uuid import uuid4 as uuid

import pytest

BLOCK_SIZE_MB = 16
FILE_COUNT = 1
FILE_SIZE_MB = 16
GENERATION_TIMEOUT_SEC = 120
RC_TEXT = """
    url: http://platform.dev.neuromation.io/api/v1
"""

GCR_UBUNTU_IMAGE_URL = 'gcr.io/light-reality-205619/ubuntu:latest'

format_list = '{type:<15}{size:<15,}{name:<}'.format


async def generate_test_data(root, count, size_mb):
    async def generate_file(name):
        exec_sha_name = 'sha1sum' if platform.platform() == 'linux' \
            else 'shasum'

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


@pytest.fixture(scope="session")
def nested_data(tmpdir_factory):
    loop = asyncio.get_event_loop()
    root_tmp_dir = tmpdir_factory.mktemp('data')
    tmp_dir = root_tmp_dir.mkdir('nested').mkdir(
        'directory').mkdir('for').mkdir('test')
    data = loop.run_until_complete(
        generate_test_data(
            tmp_dir,
            FILE_COUNT,
            FILE_SIZE_MB))
    return data[0][0], data[0][1], root_tmp_dir.strpath


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
def test_empty_directory_ls_output(run):
    _dir = f'e2e-{uuid()}'
    _path = f'/tmp/{_dir}'

    # Create directory for the test
    _, captured = run(['store', 'mkdir', _path])
    assert not captured.err
    assert captured.out == _path + '\n'

    # Ensure output of ls - empty directory shall print nothing.
    _, captured = run(['store', 'ls', _path])
    assert not captured.err
    assert captured.out.isspace()

    # Remove test dir
    _, captured = run([
            'store', 'rm', _path
        ])
    assert not captured.err


@pytest.mark.e2e
def test_e2e_shm_run_without(run, tmpdir):
    _dir_src = f'e2e-{uuid()}'
    _path_src = f'/tmp/{_dir_src}'

    _dir_dst = f'e2e-{uuid()}'
    _path_dst = f'/tmp/{_dir_dst}'

    # Create directory for the test, going to be model and result output
    run(['store', 'mkdir', _path_src])
    run(['store', 'mkdir', _path_dst])

    # Start the df test job
    command = 'bash -c "/bin/df --block-size M ' \
              '--output=target,avail /dev/shm; false"'
    _, captured = run(['model', 'train',
                       GCR_UBUNTU_IMAGE_URL,
                       'storage:/' + _path_src,
                       'storage:/' + _path_dst, command])

    # TODO (R Zubairov, 09/13/2018): once we would have wait for job
    # replace spin loop

    out = captured.out
    job_id = re.match('Job ID: (.+) Status:', out).group(1)
    start_time = time()
    while ('Status: failed' not in out) and (int(time() - start_time) < 10):
        sleep(2)
        _, captured = run(['job', 'status', job_id])
        out = captured.out

    # Remove test dir
    run(['store', 'rm', _path_src])
    run(['store', 'rm', _path_dst])

    assert '/dev/shm' in out
    assert '64M' in out


@pytest.mark.e2e
def test_e2e_shm_run_with(run, tmpdir):
    _dir_src = f'e2e-{uuid()}'
    _path_src = f'/tmp/{_dir_src}'

    _dir_dst = f'e2e-{uuid()}'
    _path_dst = f'/tmp/{_dir_dst}'

    # Create directory for the test, going to be model and result output
    run(['store', 'mkdir', _path_src])
    run(['store', 'mkdir', _path_dst])

    # Start the df test job
    command = 'bash -c "/bin/df --block-size M ' \
              '--output=target,avail /dev/shm; false"'
    _, captured = run(['model', 'train', '-x',
                       GCR_UBUNTU_IMAGE_URL,
                       'storage:/' + _path_src,
                       'storage:/' + _path_dst, command])

    # TODO (R Zubairov, 09/13/2018): once we would have wait for job
    # replace spin loop

    out = captured.out
    job_id = re.match('Job ID: (.+) Status:', out).group(1)
    start_time = time()
    while ('Status: failed' not in out) and (int(time() - start_time) < 10):
        sleep(2)
        _, captured = run(['job', 'status', job_id])
        out = captured.out

    # Remove test dir
    run(['store', 'rm', _path_src])
    run(['store', 'rm', _path_dst])

    assert '/dev/shm' in out
    assert '64M' not in out


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
    assert captured.out == urlparse('storage://' + _path
                                    + '/foo' + '\n').geturl()

    # Confirm file has been uploaded
    _, captured = run(['store', 'ls', _path])
    captured_output_list = captured.out.split('\n')
    assert 'file           16,777,216     foo' \
        in captured_output_list
    assert not captured.err

    # Download into local file and confirm checksum
    _local = join(tmpdir, 'bar')
    _, captured = run([
        'store', 'cp',
        'storage://' + _path + '/foo', _local
    ])
    assert hash_hex(_local) == checksum

    # Download into local dir and confirm checksum
    _local = join(tmpdir, 'bardir')
    _local_file = join(_local, 'foo')
    tmpdir.mkdir('bardir')
    _, captured = run([
        'store', 'cp',
        'storage://' + _path + '/foo', _local
    ])
    assert hash_hex(_local_file) == checksum

    # Remove test dir
    _, captured = run([
            'store', 'rm', _path
        ])
    assert not captured.err

    # And confirm
    _, captured = run([
            'store', 'ls', '/tmp'
        ])

    split = captured.out.split('\n')
    assert format_list(name=_dir, size=0, type='directory') not in split

    assert not captured.err


@pytest.mark.e2e
def test_e2e_copy_non_existing_platform_to_non_existing_local(run, tmpdir):
    _dir = f'e2e-{uuid()}'
    _path = f'/tmp/{_dir}'

    # Create directory for the test
    _, captured = run(['store', 'mkdir', _path])
    assert not captured.err
    assert captured.out == _path + '\n'

    # Try downloading non existing file
    _local = join(tmpdir, 'bar')
    with pytest.raises(SystemExit, match=r'127'):
        _, captured = run([
            'store', 'cp',
            'storage://' + _path + '/foo', _local
        ])

    with pytest.raises(SystemExit, match=r'127'):
        _, captured = run([
            'store', 'cp', '-r',
            'storage://' + _path + '/foo', _local
        ])

    # Remove test dir
    _, captured = run([
            'store', 'rm', _path
        ])
    assert not captured.err

    # And confirm
    _, captured = run([
            'store', 'ls', '/tmp'
        ])

    split = captured.out.split('\n')
    assert format_list(name=_dir, size=0, type='directory') not in split

    assert not captured.err


@pytest.mark.e2e
def test_e2e_copy_non_existing_platform_to_____existing_local(run, tmpdir):
    _dir = f'e2e-{uuid()}'
    _path = f'/tmp/{_dir}'

    # Create directory for the test
    _, captured = run(['store', 'mkdir', _path])
    assert not captured.err
    assert captured.out == _path + '\n'

    # Try downloading non existing file
    _local = join(tmpdir)
    with pytest.raises(SystemExit, match=r'127'):
        _, captured = run([
            'store', 'cp',
            'storage://' + _path + '/foo', _local
        ])
    assert captured.err == ''

    with pytest.raises(SystemExit, match=r'127'):
        _, captured = run([
            'store', 'cp', '-r',
            'storage://' + _path + '/foo', _local
        ])
    assert captured.err == ''

    # And confirm
    _, captured = run([
            'store', 'ls', '/tmp'
        ])

    split = captured.out.split('\n')
    assert format_list(name=_dir, size=0, type='directory') in split

    # Remove test dir
    _, captured = run([
            'store', 'rm', _path
        ])
    assert not captured.err

    # And confirm
    _, captured = run([
            'store', 'ls', '/tmp'
        ])

    split = captured.out.split('\n')
    assert format_list(name=_dir, size=0, type='directory') not in split

    assert not captured.err


@pytest.mark.e2e
def test_e2e_copy_recursive_to_platform(nested_data, run, tmpdir):
    file, checksum, dir_path = nested_data

    target_file_name = file.split('/')[-1]
    _dir = f'e2e-{uuid()}'
    _path = f'/tmp/{_dir}'

    # Create directory for the test
    _, captured = run(['store', 'mkdir', _path])
    assert not captured.err
    assert captured.out == _path + '\n'

    # Upload local file
    _, captured = run([
            'store', 'cp', '-r', dir_path, 'storage://' + _path + '/tar.tar'
        ])
    assert not captured.err
    assert captured.out == urlparse('storage://' + _path
                                    + '/' + '\n').geturl()

    # Check directory structure
    _, captured = run(['store', 'ls', f'{_path}'])
    captured_output_list = captured.out.split('\n')
    assert f'directory      0              nested' in captured_output_list
    assert not captured.err

    _, captured = run(['store', 'ls', f'{_path}/nested'])
    captured_output_list = captured.out.split('\n')
    assert f'directory      0              directory' in captured_output_list
    assert not captured.err

    _, captured = run(['store', 'ls', f'{_path}/nested/directory'])
    captured_output_list = captured.out.split('\n')
    assert f'directory      0              for' in captured_output_list
    assert not captured.err

    _, captured = run(['store', 'ls', f'{_path}/nested/directory/for'])
    captured_output_list = captured.out.split('\n')
    assert f'directory      0              test' in captured_output_list
    assert not captured.err

    # Confirm file has been uploaded
    _, captured = run(['store', 'ls', f'{_path}/nested/directory/for/test'])
    captured_output_list = captured.out.split('\n')
    assert f'file           16,777,216     {target_file_name}' \
        in captured_output_list
    assert not captured.err

    # Download into local directory and confirm checksum
    tmpdir.mkdir('bar')
    _local = join(tmpdir, 'bar')
    _, captured = run([
        'store', 'cp', '-r',
        'storage://' + _path + '/', _local
    ])
    assert hash_hex(_local + f'/nested/directory/for/'
                             f'test/{target_file_name}') == checksum

    # Remove test dir
    _, captured = run([
            'store', 'rm', _path
        ])
    assert not captured.err

    # And confirm
    _, captured = run([
            'store', 'ls', '/tmp'
        ])

    split = captured.out.split('\n')
    assert format_list(name=_dir, size=0, type='directory') not in split

    assert not captured.err
