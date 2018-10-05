import os
import re
from time import sleep, time
from uuid import uuid4 as uuid

import pytest

RC_TEXT = "url: http://platform.dev.neuromation.io/api/v1\n"\
    "auth: {token}"


UBUNTU_IMAGE_NAME = 'ubuntu:latest'


@pytest.fixture
def run(monkeypatch, capsys, tmpdir):
    import sys
    from pathlib import Path

    e2e_test_token = os.environ['CLIENT_TEST_E2E_USER_NAME']

    rc_text = RC_TEXT.format(token=e2e_test_token)
    tmpdir.join('.nmrc').open('w').write(rc_text)

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


@pytest.mark.e2e
def test_job_filtering(run, tmpdir):
    _dir_src = f'e2e-{uuid()}'
    _path_src = f'/tmp/{_dir_src}'

    _dir_dst = f'e2e-{uuid()}'
    _path_dst = f'/tmp/{_dir_dst}'

    # Create directory for the test, going to be model and result output
    run(['store', 'mkdir', f'storage://{_path_src}'])
    run(['store', 'mkdir', f'storage://{_path_dst}'])

    _, captured = run(['job', 'list', '--status', 'running'])
    store_out = captured.out
    job_ids = [x.split(' ')[0] for x in store_out.split('\n')]

    # Start the job
    command = 'bash -c "sleep 1m; false"'
    _, captured = run(['model', 'train', '-m', '20M', '-c', '0.1', '-g', '0',
                       UBUNTU_IMAGE_NAME,
                       'storage:/' + _path_src,
                       'storage:/' + _path_dst, command])
    job_id = re.match('Job ID: (.+) Status:', captured.out).group(1)

    out = 'Status: pending'
    start_time = time()
    while ('Status: pending' in out) and (int(time() - start_time) < 10):
        sleep(2)
        _, captured = run(['job', 'status', job_id])
        out = captured.out

    _, captured = run(['job', 'list', '--status', 'running'])
    store_out = captured.out
    assert command in captured.out
    job_ids2 = [x.split(' ')[0] for x in store_out.split('\n')]
    assert job_ids != job_ids2
    assert job_id in job_ids2

    _, captured = run(['job', 'kill', job_id])

    _, captured = run(['job', 'list', '--status', 'running'])
    store_out = captured.out
    job_ids2 = [x.split(' ')[0] for x in store_out.split('\n')]
    assert job_ids == job_ids2
    assert job_id not in job_ids2
