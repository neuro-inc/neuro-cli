import re
from time import sleep, time
from urllib.parse import urlparse
from uuid import uuid4 as uuid

import aiohttp
import pytest

from neuromation.cli.rc import ConfigFactory
from tests.e2e.test_e2e_utils import (
    wait_for_job_to_change_state_from,
    wait_for_job_to_change_state_to,
)


UBUNTU_IMAGE_NAME = "ubuntu:latest"
NGINX_IMAGE_NAME = "nginx:latest"


@pytest.mark.e2e
def test_job_complete_lifecycle(run, loop, tmpdir):
    _dir_src = f"e2e-{uuid()}"
    _path_src = f"/tmp/{_dir_src}"

    _dir_dst = f"e2e-{uuid()}"
    _path_dst = f"/tmp/{_dir_dst}"

    # Create directory for the test, going to be model and result output
    run(["store", "mkdir", f"storage://{_path_src}"])
    run(["store", "mkdir", f"storage://{_path_dst}"])

    # remember original set or running jobs
    _, captured = run(["job", "list", "--status", "running,pending"])
    store_out_list = captured.out.strip().split("\n")[1:]  # cut out the header line
    jobs_orig = [x.split("\t")[0] for x in store_out_list]

    # Start the jobs
    command_1 = 'bash -c "sleep 20m; false"'
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
            UBUNTU_IMAGE_NAME,
            "storage://" + _path_src,
            "storage://" + _path_dst,
            command_1,
        ]
    )
    job_id_1 = re.match("Job ID: (.+) Status:", captured.out).group(1)
    assert job_id_1.startswith("job-")
    assert job_id_1 not in jobs_orig

    command_2 = 'bash -c "sleep 20m; false"'
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
            "--http",
            "80",
            "--quiet",
            UBUNTU_IMAGE_NAME,
            "--volume",
            f"storage://{_path_src}:{_path_src}:ro",
            "--volume",
            f"storage://{_path_dst}:{_path_dst}:rw",
            command_2,
        ]
    )
    job_id_2 = captured.out.strip()
    assert job_id_2.startswith("job-")
    assert job_id_2 not in jobs_orig

    _, captured = run(
        ["job", "submit", UBUNTU_IMAGE_NAME, "--memory", "2000000000000M", "-q"]
    )
    job_id_3 = captured.out.strip()
    assert job_id_3.startswith("job-")

    # wait jobs for becoming running
    wait_for_job_to_change_state_from(
        run,
        job_id_1,
        "Status: pending",
        "Cluster doesn't have resources to fulfill request",
    )
    wait_for_job_to_change_state_from(
        run,
        job_id_2,
        "Status: pending",
        "Cluster doesn't have resources to fulfill request",
    )
    with pytest.raises(Exception) as e:
        wait_for_job_to_change_state_from(
            run,
            job_id_3,
            "Status: pending",
            "Cluster doesn't have resources to fulfill request",
        )
        assert "Cluster doesn't have resources to fulfill request" in str(e)

    wait_for_job_to_change_state_to(run, job_id_1, "Status: running")
    wait_for_job_to_change_state_to(run, job_id_2, "Status: running")
    wait_for_job_to_change_state_to(run, job_id_3, "Status: pending")

    # check running via job list
    _, captured = run(["job", "list", "--status", "running"])
    store_out = captured.out.strip()
    assert command_1 in store_out
    assert command_2 in store_out
    jobs_before_killing = [x.split("\t")[0] for x in store_out.split("\n")]
    assert job_id_1 in jobs_before_killing
    assert job_id_2 in jobs_before_killing

    # do the same with job list -q
    _, captured = run(["job", "list", "--status", "running", "-q"])
    jobs_before_killing_q = [x.strip() for x in captured.out.strip().split("\n")]
    assert job_id_1 in jobs_before_killing_q
    assert job_id_2 in jobs_before_killing_q

    # kill multiple jobs
    _, captured = run(["job", "kill", job_id_1, job_id_2, job_id_3])
    kill_output_list = [x.strip() for x in captured.out.strip().split("\n")]
    assert kill_output_list == [job_id_1, job_id_2, job_id_3]

    wait_for_job_to_change_state_from(run, job_id_1, "Status: running")
    wait_for_job_to_change_state_from(run, job_id_2, "Status: running")
    wait_for_job_to_change_state_from(run, job_id_3, "Status: pending")

    wait_for_job_to_change_state_to(run, job_id_1, "Status: succeeded")
    wait_for_job_to_change_state_to(run, job_id_2, "Status: succeeded")
    wait_for_job_to_change_state_to(run, job_id_3, "Status: failed")

    # check killed running,pending
    _, captured = run(["job", "list", "--status", "running,pending", "-q"])
    jobs_after_kill_q = [x.strip() for x in captured.out.strip().split("\n")]
    assert job_id_1 not in jobs_after_kill_q
    assert job_id_2 not in jobs_after_kill_q
    assert job_id_3 not in jobs_after_kill_q

    # check killed succeeded
    _, captured = run(["job", "list", "--status", "succeeded", "-q"])
    jobs_after_kill_q = [x.strip() for x in captured.out.strip().split("\n")]
    assert job_id_1 in jobs_after_kill_q  # were killed => manually set to succeeded
    assert job_id_2 in jobs_after_kill_q  # were killed => manually set to succeeded
    assert job_id_3 not in jobs_after_kill_q  # failed even before

    # check killed failed
    _, captured = run(["job", "list", "--status", "failed", "-q"])
    jobs_after_kill_q = [x.strip() for x in captured.out.strip().split("\n")]
    assert job_id_1 not in jobs_after_kill_q
    assert job_id_2 not in jobs_after_kill_q
    assert job_id_3 in jobs_after_kill_q

    # try to kill already killed: same output
    _, captured = run(["job", "kill", job_id_1])
    kill_output_list = [x.strip() for x in captured.out.strip().split("\n")]
    assert kill_output_list == [job_id_1]


@pytest.mark.e2e
def test_job_kill_non_existing(run, loop):
    # try to kill non existing job
    phantom_id = "NOT_A_JOB_ID"
    expected_out = f"Cannot kill job {phantom_id}: no such job {phantom_id}"
    _, captured = run(["job", "kill", phantom_id])
    killed_jobs = [x.strip() for x in captured.out.strip().split("\n")]
    assert killed_jobs == [expected_out]


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
