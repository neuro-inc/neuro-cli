import os
import re
from time import sleep
from urllib.parse import urlparse
from uuid import uuid4 as uuid

import aiohttp
import pytest

from neuromation.cli.rc import ConfigFactory
from tests.test_e2e_utils import wait_for_job_to_change_state_from

RC_TEXT = "url: http://platform.dev.neuromation.io/api/v1\n"\
    "auth: {token}"


UBUNTU_IMAGE_NAME = 'ubuntu:latest'
NGINX_IMAGE_NAME = 'nginx:latest'


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
                       'storage://' + _path_src,
                       'storage://' + _path_dst, command])
    job_id = re.match('Job ID: (.+) Status:', captured.out).group(1)

    wait_for_job_to_change_state_from(run, job_id, 'Status: pending')

    _, captured = run(['job', 'list', '--status', 'running'])
    store_out = captured.out
    assert command in captured.out
    job_ids2 = [x.split(' ')[0] for x in store_out.split('\n')]
    assert job_ids != job_ids2
    assert job_id in job_ids2

    _, captured = run(['job', 'kill', job_id])
    wait_for_job_to_change_state_from(run, job_id, 'Status: running')

    _, captured = run(['job', 'list', '--status', 'running'])
    store_out = captured.out
    job_ids2 = [x.split(' ')[0] for x in store_out.split('\n')]
    assert job_ids == job_ids2
    assert job_id not in job_ids2


@pytest.mark.e2e
def test_model_train_with_http(run, loop):
    async def get_(platform_url):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f'http://{job_id}.jobs.{platform_url}'
            ) as resp:
                assert resp.status == 200

    _dir_src = f'e2e-{uuid()}'
    _path_src = f'/tmp/{_dir_src}'

    _dir_dst = f'e2e-{uuid()}'
    _path_dst = f'/tmp/{_dir_dst}'

    # Create directory for the test, going to be model and result output
    run(['store', 'mkdir', f'storage://{_path_src}'])
    run(['store', 'mkdir', f'storage://{_path_dst}'])

    # Start the job
    command = '/usr/sbin/nginx -g "daemon off;"'
    _, captured = run(['model', 'train', '-m', '20M', '-c', '0.1', '-g', '0',
                       '--http', '80',
                       NGINX_IMAGE_NAME,
                       'storage://' + _path_src,
                       'storage://' + _path_dst,
                       command])
    job_id = re.match('Job ID: (.+) Status:', captured.out).group(1)
    wait_for_job_to_change_state_from(run, job_id, 'Status: pending')

    sleep(5)
    config = ConfigFactory.load()
    parsed_url = urlparse(config.url)

    loop.run_until_complete(get_(parsed_url.netloc))

    _, captured = run(['job', 'kill', job_id])
    wait_for_job_to_change_state_from(run, job_id, 'Status: running')
