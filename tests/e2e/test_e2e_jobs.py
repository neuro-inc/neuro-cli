import asyncio
import os
import re
from time import sleep, time
from uuid import uuid4

import aiohttp
import pytest
from aiohttp.test_utils import unused_port

from neuromation.api import (
    Image,
    JobStatus,
    NetworkPortForwarding,
    Resources,
    get as api_get,
)
from neuromation.utils import run as run_async


UBUNTU_IMAGE_NAME = "ubuntu:latest"
NGINX_IMAGE_NAME = "nginx:latest"
MIN_PORT = 49152
MAX_PORT = 65535


@pytest.mark.e2e
def test_job_lifecycle(helper):
    # Remember original running jobs
    captured = helper.run_cli(
        ["job", "ls", "--status", "running", "--status", "pending"]
    )
    store_out_list = captured.out.split("\n")[1:]
    jobs_orig = [x.split("  ")[0] for x in store_out_list]

    # Run a new job
    job_name = f"test-job-name-{uuid4()}"
    command = 'bash -c "sleep 10m; false"'
    captured = helper.run_cli(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "-g",
            "0",
            "--http",
            "80",
            "--non-preemptible",
            "--no-wait-start",
            "--name",
            job_name,
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)
    assert job_id.startswith("job-")
    assert job_id not in jobs_orig
    assert f"Name: {job_name}" in captured.out
    assert re.search("Http URL: http", captured.out), captured.out

    # Check it is in a running,pending job list now
    captured = helper.run_cli(
        ["job", "ls", "--status", "running", "--status", "pending"]
    )
    store_out_list = captured.out.split("\n")[1:]
    jobs_updated = [x.split("  ")[0] for x in store_out_list]
    assert job_id in jobs_updated

    # Wait until the job is running
    helper.wait_job_change_state_to(job_id, JobStatus.RUNNING)

    # Check that it is in a running job list
    captured = helper.run_cli(["job", "ls", "--status", "running"])
    store_out = captured.out
    assert job_id in store_out
    # Check that the command is in the list
    assert command in store_out

    # Check that no command is in the list if quite
    captured = helper.run_cli(["job", "ls", "--status", "running", "-q"])
    store_out = captured.out
    assert job_id in store_out
    assert command not in store_out

    # Kill the job by name
    captured = helper.run_cli(["job", "kill", job_name])

    # Currently we check that the job is not running anymore
    # TODO(adavydow): replace to succeeded check when racecon in
    # platform-api fixed.
    helper.wait_job_change_state_from(job_id, JobStatus.RUNNING)

    # Check that it is not in a running job list anymore
    captured = helper.run_cli(["job", "ls", "--status", "running"])
    store_out = captured.out
    assert job_id not in store_out

    # Check job ls by name
    captured = helper.run_cli(["job", "ls", "-n", job_name, "-s", "succeeded"])
    store_out = captured.out
    assert job_id in store_out
    assert job_name in store_out

    # Check job status by id
    captured = helper.run_cli(["job", "status", job_id])
    store_out = captured.out
    assert store_out.startswith(f"Job: {job_id}\nName: {job_name}")

    # Check job status by name
    captured = helper.run_cli(["job", "status", job_name])
    store_out = captured.out
    assert store_out.startswith(f"Job: {job_id}\nName: {job_name}")


@pytest.mark.e2e
def test_job_description(helper):
    # Remember original running jobs
    captured = helper.run_cli(
        ["job", "ls", "--status", "running", "--status", "pending"]
    )
    store_out_list = captured.out.split("\n")[1:]
    jobs_orig = [x.split("  ")[0] for x in store_out_list]
    description = "Test description for a job"
    # Run a new job
    command = 'bash -c "sleep 10m; false"'
    captured = helper.run_cli(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "-g",
            "0",
            "--http",
            "80",
            "--description",
            description,
            "--non-preemptible",
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)

    # Check it was not running before
    assert job_id.startswith("job-")
    assert job_id not in jobs_orig

    # Check it is in a running,pending job list now
    captured = helper.run_cli(
        ["job", "ls", "--status", "running", "--status", "pending"]
    )
    store_out_list = captured.out.split("\n")[1:]
    jobs_updated = [x.split("  ")[0] for x in store_out_list]
    assert job_id in jobs_updated

    # Wait until the job is running
    helper.wait_job_change_state_to(job_id, JobStatus.RUNNING, JobStatus.FAILED)

    # Check that it is in a running job list
    captured = helper.run_cli(["job", "ls", "--status", "running"])
    store_out = captured.out
    assert job_id in store_out
    # Check that description is in the list
    assert description in store_out
    assert command in store_out

    # Check that no description is in the list if quite
    captured = helper.run_cli(["job", "ls", "--status", "running", "-q"])
    store_out = captured.out
    assert job_id in store_out
    assert description not in store_out
    assert command not in store_out

    # Kill the job
    captured = helper.run_cli(["job", "kill", job_id])

    # Currently we check that the job is not running anymore
    # TODO(adavydow): replace to succeeded check when racecon in
    # platform-api fixed.
    helper.wait_job_change_state_from(job_id, JobStatus.RUNNING)

    # Check that it is not in a running job list anymore
    captured = helper.run_cli(["job", "ls", "--status", "running"])
    store_out = captured.out
    assert job_id not in store_out


@pytest.mark.e2e
def test_job_kill_non_existing(helper):
    # try to kill non existing job
    phantom_id = "NOT_A_JOB_ID"
    expected_out = f"Cannot kill job {phantom_id}"
    captured = helper.run_cli(["job", "kill", phantom_id])
    killed_jobs = [x.strip() for x in captured.out.split("\n")]
    assert len(killed_jobs) == 1
    assert killed_jobs[0].startswith(expected_out)


@pytest.mark.e2e
def test_e2e_no_env(helper):
    bash_script = 'echo "begin"$VAR"end"  | grep beginend'
    command = f"bash -c '{bash_script}'"
    captured = helper.run_cli(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "-g",
            "0",
            "--non-preemptible",
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )

    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    helper.wait_job_change_state_from(job_id, JobStatus.PENDING)
    helper.wait_job_change_state_from(job_id, JobStatus.RUNNING)

    helper.assert_job_state(job_id, JobStatus.SUCCEEDED)


@pytest.mark.e2e
def test_e2e_env(helper):
    bash_script = 'echo "begin"$VAR"end"  | grep beginVALend'
    command = f"bash -c '{bash_script}'"
    captured = helper.run_cli(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "-g",
            "0",
            "-e",
            "VAR=VAL",
            "--non-preemptible",
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )

    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    helper.wait_job_change_state_from(job_id, JobStatus.PENDING)
    helper.wait_job_change_state_from(job_id, JobStatus.RUNNING)

    helper.assert_job_state(job_id, JobStatus.SUCCEEDED)


@pytest.mark.e2e
def test_e2e_env_from_local(helper):
    os.environ["VAR"] = "VAL"
    bash_script = 'echo "begin"$VAR"end"  | grep beginVALend'
    command = f"bash -c '{bash_script}'"
    captured = helper.run_cli(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "-g",
            "0",
            "-e",
            "VAR",
            "--non-preemptible",
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )

    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    helper.wait_job_change_state_from(job_id, JobStatus.PENDING)
    helper.wait_job_change_state_from(job_id, JobStatus.RUNNING)

    helper.assert_job_state(job_id, JobStatus.SUCCEEDED)


@pytest.mark.e2e
def test_e2e_multiple_env(helper):
    bash_script = 'echo begin"$VAR""$VAR2"end  | grep beginVALVAL2end'
    command = f"bash -c '{bash_script}'"
    captured = helper.run_cli(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "-g",
            "0",
            "-e",
            "VAR=VAL",
            "-e",
            "VAR2=VAL2",
            "--non-preemptible",
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )

    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    helper.wait_job_change_state_from(job_id, JobStatus.PENDING)
    helper.wait_job_change_state_from(job_id, JobStatus.RUNNING)

    helper.assert_job_state(job_id, JobStatus.SUCCEEDED)


@pytest.mark.e2e
def test_e2e_multiple_env_from_file(helper, tmp_path):
    env_file = tmp_path / "env_file"
    env_file.write_text("VAR2=LAV2\nVAR3=VAL3\n")
    bash_script = 'echo begin"$VAR""$VAR2""$VAR3"end  | grep beginVALVAL2VAL3end'
    command = f"bash -c '{bash_script}'"
    captured = helper.run_cli(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "-g",
            "0",
            "-e",
            "VAR=VAL",
            "-e",
            "VAR2=VAL2",
            "--env-file",
            str(env_file),
            "--non-preemptible",
            "--no-wait-start",
            "-q",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )

    job_id = captured.out

    helper.wait_job_change_state_from(job_id, JobStatus.PENDING)
    helper.wait_job_change_state_from(job_id, JobStatus.RUNNING)

    helper.assert_job_state(job_id, JobStatus.SUCCEEDED)


@pytest.mark.e2e
def test_e2e_ssh_exec_true(helper):
    job_name = f"test-job-{uuid4()}"
    command = 'bash -c "sleep 15m; false"'
    captured = helper.run_cli(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "--non-preemptible",
            "--no-wait-start",
            "-n",
            job_name,
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    helper.wait_job_change_state_to(job_id, JobStatus.RUNNING)

    captured = helper.run_cli(["job", "exec", "--no-key-check", job_id, "true"])
    assert captured.out == ""

    captured = helper.run_cli(["job", "exec", "--no-key-check", job_name, "true"])
    assert captured.out == ""


@pytest.mark.e2e
def test_e2e_ssh_exec_false(helper):
    command = 'bash -c "sleep 15m; false"'
    captured = helper.run_cli(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "--non-preemptible",
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    helper.wait_job_change_state_to(job_id, JobStatus.RUNNING)

    with pytest.raises(SystemExit) as cm:
        helper.run_cli(["job", "exec", "--no-key-check", job_id, "false"])
    assert cm.value.code == 1


@pytest.mark.e2e
def test_e2e_ssh_exec_no_cmd(helper):
    command = 'bash -c "sleep 15m; false"'
    captured = helper.run_cli(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "--non-preemptible",
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    helper.wait_job_change_state_to(job_id, JobStatus.RUNNING)

    with pytest.raises(SystemExit) as cm:
        helper.run_cli(["job", "exec", "--no-key-check", job_id])
    assert cm.value.code == 2


@pytest.mark.e2e
def test_e2e_ssh_exec_echo(helper):
    command = 'bash -c "sleep 15m; false"'
    captured = helper.run_cli(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "--non-preemptible",
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    helper.wait_job_change_state_to(job_id, JobStatus.RUNNING)

    captured = helper.run_cli(["job", "exec", "--no-key-check", job_id, "echo 1"])
    assert captured.out == "1"


@pytest.mark.e2e
def test_e2e_ssh_exec_no_tty(helper):
    command = 'bash -c "sleep 15m; false"'
    captured = helper.run_cli(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "--non-preemptible",
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    helper.wait_job_change_state_to(job_id, JobStatus.RUNNING)

    with pytest.raises(SystemExit) as cm:
        helper.run_cli(["job", "exec", "--no-key-check", job_id, "[ -t 1 ]"])
    assert cm.value.code == 1


@pytest.mark.e2e
def test_e2e_ssh_exec_tty(helper):
    command = 'bash -c "sleep 15m; false"'
    captured = helper.run_cli(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "--non-preemptible",
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    helper.wait_job_change_state_to(job_id, JobStatus.RUNNING)

    captured = helper.run_cli(
        ["job", "exec", "-t", "--no-key-check", job_id, "[ -t 1 ]"]
    )
    assert captured.out == ""


@pytest.mark.e2e
def test_e2e_ssh_exec_no_job(helper):
    with pytest.raises(SystemExit) as cm:
        helper.run_cli(["job", "exec", "--no-key-check", "job_id", "true"])
    assert cm.value.code == 127


@pytest.mark.e2e
def test_e2e_ssh_exec_dead_job(helper):
    command = "true"
    captured = helper.run_cli(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "--non-preemptible",
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    helper.wait_job_change_state_from(job_id, JobStatus.PENDING)
    helper.wait_job_change_state_from(job_id, JobStatus.RUNNING)

    with pytest.raises(SystemExit) as cm:
        helper.run_cli(["job", "exec", "--no-key-check", job_id, "true"])
    assert cm.value.code == 127


@pytest.fixture
def nginx_job(helper):
    command = 'timeout 15m /usr/sbin/nginx -g "daemon off;"'
    captured = helper.run_cli(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "-g",
            "0",
            "--non-preemptible",
            NGINX_IMAGE_NAME,
            command,
        ]
    )
    job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)
    helper.wait_job_change_state_from(job_id, JobStatus.PENDING, JobStatus.FAILED)

    yield job_id

    helper.run_cli(["job", "kill", job_id])


@pytest.fixture
async def nginx_job_async(nmrc_path, loop):
    async with api_get(path=nmrc_path) as client:
        command = "timeout 15m python -m http.server 22"
        job = await client.jobs.submit(
            image=Image("python:latest", command=command),
            resources=Resources.create(0.1, None, None, 20, True),
            network=NetworkPortForwarding.from_cli(None, 22),
            is_preemptible=False,
            volumes=None,
            description="test NGINX job",
            env=[],
        )
        try:
            for i in range(60):
                status = await client.jobs.status(job.id)
                if status.status == JobStatus.RUNNING:
                    break
                await asyncio.sleep(1)
            else:
                raise AssertionError("Cannot start NGINX job")
            yield job.id
        finally:
            await client.jobs.kill(job.id)


@pytest.mark.e2e
async def test_port_forward(nmrc_path, nginx_job_async):
    loop_sleep = 1
    service_wait_time = 60

    async def get_(url):
        status = 999
        start_time = time()
        async with aiohttp.ClientSession() as session:
            while status != 200 and (int(time() - start_time) < service_wait_time):
                try:
                    async with session.get(url) as resp:
                        status = resp.status
                except aiohttp.ClientConnectionError:
                    status = 599
                if status != 200:
                    sleep(loop_sleep)
        return status

    loop = asyncio.get_event_loop()
    async with api_get(path=nmrc_path) as client:
        forwarder = None
        try:
            port = unused_port()
            # We test client instead of run_cli as asyncio subprocesses do
            # not work if run from thread other than main.
            forwarder = loop.create_task(
                client.jobs.port_forward(nginx_job_async, True, port, 22)
            )

            url = f"http://127.0.0.1:{port}"
            probe = await get_(url)
            assert probe == 200
        finally:
            forwarder.cancel()
            with pytest.raises(asyncio.CancelledError):
                await forwarder


@pytest.mark.e2e
def test_job_submit_http_auth(helper, secret_job):
    loop_sleep = 1
    service_wait_time = 60

    async def _test_http_auth_redirect(url):
        start_time = time()
        async with aiohttp.ClientSession() as session:
            while time() - start_time < service_wait_time:
                try:
                    async with session.get(url, allow_redirects=True) as resp:
                        if resp.status == 200 and re.match(
                            r".+\.auth0\.com$", resp.url.host
                        ):
                            break
                except aiohttp.ClientConnectionError:
                    pass
                sleep(loop_sleep)
            else:
                raise AssertionError("HTTP Auth not detected")

    async def _test_http_auth_with_cookie(url, cookies, secret):
        start_time = time()
        async with aiohttp.ClientSession(cookies=cookies) as session:
            while time() - start_time < service_wait_time:
                try:
                    async with session.get(url, allow_redirects=False) as resp:
                        if resp.status == 200:
                            body = await resp.text()
                            if secret == body.strip():
                                break
                        raise AssertionError("Secret not match")
                except aiohttp.ClientConnectionError:
                    pass
                sleep(loop_sleep)
            else:
                raise AssertionError("Cannot fetch secret via forwarded http")

    http_job = secret_job(http_port=True, http_auth=True)
    ingress_secret_url = http_job["ingress_url"].with_path("/secret.txt")

    run_async(_test_http_auth_redirect(ingress_secret_url))

    cookies = {"dat": helper.token}
    run_async(
        _test_http_auth_with_cookie(ingress_secret_url, cookies, http_job["secret"])
    )


@pytest.mark.e2e
def test_job_run(helper):
    # Run a new job
    command = 'bash -c "sleep 10m; false"'
    captured = helper.run_cli(
        [
            "job",
            "run",
            "-q",
            "-s",
            "cpu-small",
            "--non-preemptible",
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    job_id = captured.out

    # Wait until the job is running
    helper.wait_job_change_state_to(job_id, JobStatus.RUNNING)

    # Kill the job
    captured = helper.run_cli(["job", "kill", job_id])

    # Currently we check that the job is not running anymore
    # TODO(adavydow): replace to succeeded check when racecon in
    # platform-api fixed.
    helper.wait_job_change_state_from(job_id, JobStatus.RUNNING)
