import re
from time import sleep, time
from urllib.parse import urlparse
from uuid import uuid4 as uuid

import aiohttp
import pytest

from neuromation.cli.rc import ConfigFactory
from tests.e2e.test_e2e_utils import wait_for_job_to_change_state_from


UBUNTU_IMAGE_NAME = "ubuntu:latest"
NGINX_IMAGE_NAME = "nginx:latest"


@pytest.mark.e2e
def test_job_complete_lifecycle(run, tmpdir):
    _dir_src = f"e2e-{uuid()}"
    _path_src = f"/tmp/{_dir_src}"

    _dir_dst = f"e2e-{uuid()}"
    _path_dst = f"/tmp/{_dir_dst}"

    # Create directory for the test, going to be model and result output
    run(["store", "mkdir", f"storage://{_path_src}"])
    run(["store", "mkdir", f"storage://{_path_dst}"])

    # remember original set or running jobs
    _, captured = run(["job", "list", "--status", "running"])
    store_out_list = captured.out.strip().split("\n")[1:]  # cut out the header line
    job_ids_orig = [x.split("\t")[0] for x in store_out_list if x]

    # Start the jobs
    command_first = 'bash -c "sleep 1m; false"'
    _, captured = run(
        [
            "model",
            "train",
            "-m",
            "20M",
            "-c",
            "0.1",
            "-g",
            "0",
            UBUNTU_IMAGE_NAME,
            "storage://" + _path_src,
            "storage://" + _path_dst,
            command_first,
        ]
    )
    job_id_first = re.match("Job ID: (.+) Status:", captured.out).group(1)
    assert job_id_first.startswith("job-")
    command_second = 'bash -c "sleep 2m; false"'
    _, captured = run(
        [
            "job",
            "submit",
            "--cpu",
            "0.1",
            "--memory",
            "20M",
            "--gpu",
            "0",
            "--quiet",
            UBUNTU_IMAGE_NAME,
            "--volume",
            f"storage://{_path_src}:{_path_src}:ro",
            "--volume",
            f"storage://{_path_dst}:{_path_dst}:rw",
            command_second,
        ]
    )
    job_id_second = captured.out.strip()
    assert job_id_second.startswith("job-")

    _, captured = run(
        ["job", "submit", UBUNTU_IMAGE_NAME, "--memory", "2000000000000M", "-q"]
    )
    job_id_third = captured.out.strip()
    assert job_id_third.startswith("job-")

    # wait jobs for becoming running
    wait_for_job_to_change_state_from(
        run,
        job_id_first,
        "Status: pending",
        "Cluster doesn't have resources to fulfill request",
    )
    wait_for_job_to_change_state_from(
        run,
        job_id_second,
        "Status: pending",
        "Cluster doesn't have resources to fulfill request",
    )
    with pytest.raises(Exception) as e:
        wait_for_job_to_change_state_from(
            run,
            job_id_third,
            "Status: pending",
            "Cluster doesn't have resources to fulfill request",
        )
        assert "Cluster doesn't have resources to fulfill request" in str(e)

    # check running
    _, captured = run(["job", "list", "--status", "running"])
    store_out = captured.out.strip()
    assert command_first in store_out
    assert command_second in store_out
    store_out_list = store_out.split("\n")[1:]  # cut out the header line
    job_ids_before_killing = [x.split("\t")[0] for x in store_out_list if x]
    assert job_id_first in job_ids_before_killing
    assert job_id_second in job_ids_before_killing
    assert job_ids_orig != job_ids_before_killing
    # test the job list -q
    _, captured = run(["job", "list", "--status", "running", "-q"])
    job_ids_before_killing_quiet = [x.strip() for x in captured.out.split("\n") if x]
    assert job_id_first in job_ids_before_killing_quiet
    assert job_id_second in job_ids_before_killing_quiet

    # kill multiple
    _, captured = run(["job", "kill", job_id_first, job_id_second, job_id_third])
    kill_output_list = [x.strip() for x in captured.out.split("\n") if x]
    assert len(kill_output_list) == 3
    assert job_id_first in kill_output_list
    assert job_id_second in kill_output_list
    assert job_id_third in kill_output_list
    wait_for_job_to_change_state_from(run, job_id_first, "Status: running")
    wait_for_job_to_change_state_from(run, job_id_second, "Status: running")
    wait_for_job_to_change_state_from(run, job_id_third, "Status: pending")

    # check killed
    _, captured = run(["job", "list", "--status", "running", "-q"])
    job_ids_after_kill_quiet = [x.strip() for x in captured.out.split("\n") if x]
    assert job_id_first not in job_ids_after_kill_quiet
    assert job_id_second not in job_ids_after_kill_quiet
    assert job_id_third not in job_ids_after_kill_quiet

    # try to kill already killed
    _, captured = run(["job", "kill", job_id_first])
    assert job_id_first == captured.out.strip()


@pytest.mark.e2e
def test_job_kill_non_existing(run, loop):
    # try to kill non existing job
    phantom_id = "NOT_A_JOB_ID"
    expected_out = f"Cannot kill job {phantom_id}: no such job {phantom_id}"
    _, captured = run(["job", "kill", phantom_id])
    assert captured.out.strip() == expected_out


@pytest.mark.e2e
def test_model_train_with_http(run, loop):
    loop_sleep = 1
    service_wait_time = 60

    async def get_(platform_url):
        succeeded = None
        start_time = time()
        while not succeeded and (int(time() - start_time) < service_wait_time):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{job_id}.jobs.{platform_url}") as resp:
                    succeeded = resp.status == 200
            if not succeeded:
                sleep(loop_sleep)
        return succeeded

    _dir_src = f"e2e-{uuid()}"
    _path_src = f"/tmp/{_dir_src}"

    _dir_dst = f"e2e-{uuid()}"
    _path_dst = f"/tmp/{_dir_dst}"

    # Create directory for the test, going to be model and result output
    run(["store", "mkdir", f"storage://{_path_src}"])
    run(["store", "mkdir", f"storage://{_path_dst}"])

    # Start the job
    command = '/usr/sbin/nginx -g "daemon off;"'
    _, captured = run(
        [
            "model",
            "train",
            "-m",
            "20M",
            "-c",
            "0.1",
            "-g",
            "0",
            "--http",
            "80",
            NGINX_IMAGE_NAME,
            "storage://" + _path_src,
            "storage://" + _path_dst,
            command,
            "-d",
            "simple test job",
        ]
    )
    job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)
    wait_for_job_to_change_state_from(run, job_id, "Status: pending")

    config = ConfigFactory.load()
    parsed_url = urlparse(config.url)

    assert loop.run_until_complete(get_(parsed_url.netloc))

    _, captured = run(["job", "kill", job_id])
    wait_for_job_to_change_state_from(run, job_id, "Status: running")


@pytest.mark.e2e
def test_model_without_command(run, loop):
    loop_sleep = 1
    service_wait_time = 60

    async def get_(platform_url):
        succeeded = None
        start_time = time()
        while not succeeded and (int(time() - start_time) < service_wait_time):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{job_id}.jobs.{platform_url}") as resp:
                    succeeded = resp.status == 200
            if not succeeded:
                sleep(loop_sleep)
        return succeeded

    _dir_src = f"e2e-{uuid()}"
    _path_src = f"/tmp/{_dir_src}"

    _dir_dst = f"e2e-{uuid()}"
    _path_dst = f"/tmp/{_dir_dst}"

    # Create directory for the test, going to be model and result output
    run(["store", "mkdir", f"storage://{_path_src}"])
    run(["store", "mkdir", f"storage://{_path_dst}"])

    # Start the job
    _, captured = run(
        [
            "model",
            "train",
            "-m",
            "20M",
            "-c",
            "0.1",
            "-g",
            "0",
            "--http",
            "80",
            NGINX_IMAGE_NAME,
            "storage://" + _path_src,
            "storage://" + _path_dst,
            "-d",
            "simple test job",
        ]
    )
    job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)
    wait_for_job_to_change_state_from(run, job_id, "Status: pending")

    config = ConfigFactory.load()
    parsed_url = urlparse(config.url)

    assert loop.run_until_complete(get_(parsed_url.netloc))

    _, captured = run(["job", "kill", job_id])
    wait_for_job_to_change_state_from(run, job_id, "Status: running")
