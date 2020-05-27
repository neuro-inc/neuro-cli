import asyncio
import os
import re
import subprocess
import sys
from contextlib import suppress
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep, time
from typing import Any, AsyncIterator, Callable, Dict, List, Tuple
from uuid import uuid4

import aiodocker
import aiohttp
import pytest
from aiohttp.test_utils import unused_port
from yarl import URL

from neuromation.api import Container, JobStatus, RemoteImage, Resources, get as api_get
from neuromation.cli.asyncio_utils import run
from tests.e2e.conftest import CLIENT_TIMEOUT, Helper
from tests.e2e.utils import JOB_TINY_CONTAINER_PARAMS, JOB_TINY_CONTAINER_PRESET


pytestmark = pytest.mark.e2e_job

ALPINE_IMAGE_NAME = "alpine:latest"
UBUNTU_IMAGE_NAME = "ubuntu:latest"
NGINX_IMAGE_NAME = "nginx:latest"
TEST_IMAGE_NAME = "neuro-cli-test"
MIN_PORT = 49152
MAX_PORT = 65535
EXEC_TIMEOUT = 180


@pytest.mark.e2e
def test_job_submit(helper: Helper) -> None:

    job_name = f"test-job-{os.urandom(5).hex()}"

    # Kill another active jobs with same name, if any
    # Pass --owner because --name without --owner is too slow for admin users.
    captured = helper.run_cli(
        ["-q", "job", "ls", "--owner", helper.username, "--name", job_name]
    )
    if captured.out:
        jobs_same_name = captured.out.split("\n")
        assert len(jobs_same_name) == 1, f"found multiple active jobs named {job_name}"
        job_id = jobs_same_name[0]
        helper.kill_job(job_id)

    # Remember original running jobs
    captured = helper.run_cli(
        ["job", "ls", "--status", "running", "--status", "pending"]
    )
    store_out_list = captured.out.split("\n")[1:]
    jobs_orig = [x.split("  ")[0] for x in store_out_list]

    captured = helper.run_cli(
        [
            "job",
            "submit",
            *JOB_TINY_CONTAINER_PARAMS,
            "--http",
            "80",
            "--non-preemptible",
            "--no-wait-start",
            "--restart",
            "never",
            "--name",
            job_name,
            UBUNTU_IMAGE_NAME,
            # use unrolled notation to check shlex.join()
            "bash",
            "-c",
            "sleep 10m; false",
        ]
    )
    match = re.match("Job ID: (.+) Status:", captured.out)
    assert match is not None
    job_id = match.group(1)
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
    assert "bash -c 'sleep 10m; false'" in store_out
    helper.kill_job(job_id, wait=False)


@pytest.mark.e2e
def test_job_description(helper: Helper) -> None:
    # Remember original running jobs
    captured = helper.run_cli(
        ["job", "ls", "--status", "running", "--status", "pending"]
    )
    store_out_list = captured.out.split("\n")[1:]
    jobs_orig = [x.split("  ")[0] for x in store_out_list]
    description = "Test description for a job"
    # Run a new job
    command = "bash -c 'sleep 10m; false'"
    captured = helper.run_cli(
        [
            "job",
            "submit",
            *JOB_TINY_CONTAINER_PARAMS,
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
    match = re.match("Job ID: (.+) Status:", captured.out)
    assert match is not None
    job_id = match.group(1)

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
    captured = helper.run_cli(["-q", "job", "ls", "--status", "running"])
    store_out = captured.out
    assert job_id in store_out
    assert description not in store_out
    assert command not in store_out
    helper.kill_job(job_id, wait=False)


@pytest.mark.e2e
def test_job_tags(helper: Helper) -> None:
    tags = [f"test-tag:{uuid4()}", "test-tag:common"]
    tag_options = [key for pair in [("--tag", t) for t in tags] for key in pair]

    command = "sleep 10m"
    captured = helper.run_cli(
        [
            "job",
            "run",
            "-s",
            JOB_TINY_CONTAINER_PRESET,
            *tag_options,
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    match = re.match("Job ID: (.+) Status:", captured.out)
    assert match is not None
    job_id = match.group(1)

    captured = helper.run_cli(["ps", *tag_options])
    store_out_list = captured.out.split("\n")[1:]
    jobs = [x.split("  ")[0] for x in store_out_list]
    assert job_id in jobs

    captured = helper.run_cli(["job", "tags"])
    tags_listed = captured.out.split("\n")
    assert set(tags) <= set(tags_listed)


@pytest.mark.e2e
def test_job_filter_by_date_range(helper: Helper) -> None:
    captured = helper.run_cli(
        [
            "job",
            "run",
            "-s",
            JOB_TINY_CONTAINER_PRESET,
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            "sleep 300",
        ]
    )
    match = re.match("Job ID: (.+) Status:", captured.out)
    assert match is not None
    job_id = match.group(1)
    now = datetime.now()
    delta = timedelta(minutes=10)

    captured = helper.run_cli(["ps", "--since", (now - delta).isoformat()])
    store_out_list = captured.out.split("\n")[1:]
    jobs = [x.split("  ")[0] for x in store_out_list]
    assert job_id in jobs

    captured = helper.run_cli(["ps", "--since", (now + delta).isoformat()])
    store_out_list = captured.out.split("\n")[1:]
    jobs = [x.split("  ")[0] for x in store_out_list]
    assert job_id not in jobs

    captured = helper.run_cli(["ps", "--until", (now - delta).isoformat()])
    store_out_list = captured.out.split("\n")[1:]
    jobs = [x.split("  ")[0] for x in store_out_list]
    assert job_id not in jobs

    captured = helper.run_cli(["ps", "--until", (now + delta).isoformat()])
    store_out_list = captured.out.split("\n")[1:]
    jobs = [x.split("  ")[0] for x in store_out_list]
    assert job_id in jobs


@pytest.mark.e2e
def test_job_kill_non_existing(helper: Helper) -> None:
    # try to kill non existing job
    phantom_id = "not-a-job-id"
    expected_out = f"Cannot kill job {phantom_id}"
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(["job", "kill", phantom_id])
    assert cm.value.returncode == 1
    assert cm.value.stdout == ""
    killed_jobs = cm.value.stderr.splitlines()
    assert len(killed_jobs) == 1, killed_jobs
    assert killed_jobs[0].startswith(expected_out)


@pytest.mark.e2e
def test_e2e_no_env(helper: Helper) -> None:
    bash_script = 'echo "begin"$VAR"end"  | grep beginend'
    command = f"bash -c '{bash_script}'"
    captured = helper.run_cli(
        [
            "job",
            "submit",
            *JOB_TINY_CONTAINER_PARAMS,
            "--non-preemptible",
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )

    out = captured.out
    match = re.match("Job ID: (.+) Status:", out)
    assert match is not None
    job_id = match.group(1)

    helper.wait_job_change_state_from(job_id, JobStatus.PENDING)
    helper.wait_job_change_state_from(job_id, JobStatus.RUNNING)

    helper.assert_job_state(job_id, JobStatus.SUCCEEDED)


@pytest.mark.e2e
def test_e2e_env(helper: Helper) -> None:
    bash_script = 'echo "begin"$VAR"end"  | grep beginVALend'
    command = f"bash -c '{bash_script}'"
    captured = helper.run_cli(
        [
            "job",
            "submit",
            *JOB_TINY_CONTAINER_PARAMS,
            "-e",
            "VAR=VAL",
            "--non-preemptible",
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )

    out = captured.out
    match = re.match("Job ID: (.+) Status:", out)
    assert match is not None
    job_id = match.group(1)

    helper.wait_job_change_state_from(job_id, JobStatus.PENDING)
    helper.wait_job_change_state_from(job_id, JobStatus.RUNNING)

    helper.assert_job_state(job_id, JobStatus.SUCCEEDED)


@pytest.mark.e2e
def test_e2e_env_from_local(helper: Helper) -> None:
    os.environ["VAR"] = "VAL"
    bash_script = 'echo "begin"$VAR"end"  | grep beginVALend'
    command = f"bash -c '{bash_script}'"
    captured = helper.run_cli(
        [
            "job",
            "submit",
            *JOB_TINY_CONTAINER_PARAMS,
            "-e",
            "VAR",
            "--non-preemptible",
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )

    out = captured.out
    match = re.match("Job ID: (.+) Status:", out)
    assert match is not None
    job_id = match.group(1)

    helper.wait_job_change_state_from(job_id, JobStatus.PENDING)
    helper.wait_job_change_state_from(job_id, JobStatus.RUNNING)

    helper.assert_job_state(job_id, JobStatus.SUCCEEDED)


@pytest.mark.e2e
def test_e2e_multiple_env(helper: Helper) -> None:
    bash_script = 'echo begin"$VAR""$VAR2"end  | grep beginVALVAL2end'
    command = f"bash -c '{bash_script}'"
    captured = helper.run_cli(
        [
            "job",
            "submit",
            *JOB_TINY_CONTAINER_PARAMS,
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
    match = re.match("Job ID: (.+) Status:", out)
    assert match is not None
    job_id = match.group(1)

    helper.wait_job_change_state_from(job_id, JobStatus.PENDING)
    helper.wait_job_change_state_from(job_id, JobStatus.RUNNING)

    helper.assert_job_state(job_id, JobStatus.SUCCEEDED)


@pytest.mark.e2e
def test_e2e_multiple_env_from_file(helper: Helper, tmp_path: Path) -> None:
    env_file = tmp_path / "env_file"
    env_file.write_text("VAR2=LAV2\nVAR3=VAL3\n")
    bash_script = 'echo begin"$VAR""$VAR2""$VAR3"end  | grep beginVALVAL2VAL3end'
    command = f"bash -c '{bash_script}'"
    captured = helper.run_cli(
        [
            "-q",
            "job",
            "submit",
            *JOB_TINY_CONTAINER_PARAMS,
            "-e",
            "VAR=VAL",
            "-e",
            "VAR2=VAL2",
            "--env-file",
            str(env_file),
            "--non-preemptible",
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )

    job_id = captured.out

    helper.wait_job_change_state_from(job_id, JobStatus.PENDING)
    helper.wait_job_change_state_from(job_id, JobStatus.RUNNING)

    helper.assert_job_state(job_id, JobStatus.SUCCEEDED)


@pytest.mark.e2e
def test_e2e_ssh_exec_true(helper: Helper) -> None:
    job_name = f"test-job-{str(uuid4())[:8]}"
    command = 'bash -c "sleep 15m; false"'
    job_id = helper.run_job_and_wait_state(UBUNTU_IMAGE_NAME, command, name=job_name)

    captured = helper.run_cli(
        [
            "job",
            "exec",
            "--no-tty",
            "--no-key-check",
            "--timeout",
            str(EXEC_TIMEOUT),
            job_id,
            # use unrolled notation to check shlex.join()
            "bash",
            "-c",
            "echo ok; true",
        ]
    )
    assert captured.out == "ok"
    helper.kill_job(job_id, wait=False)


@pytest.mark.e2e
def test_e2e_ssh_exec_false(helper: Helper) -> None:
    command = 'bash -c "sleep 15m; false"'
    job_id = helper.run_job_and_wait_state(UBUNTU_IMAGE_NAME, command)

    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(
            [
                "job",
                "exec",
                "--no-tty",
                "--no-key-check",
                "--timeout",
                str(EXEC_TIMEOUT),
                job_id,
                "false",
            ]
        )
    assert cm.value.returncode == 1
    helper.kill_job(job_id, wait=False)


@pytest.mark.e2e
def test_e2e_ssh_exec_no_cmd(helper: Helper) -> None:
    command = 'bash -c "sleep 15m; false"'
    job_id = helper.run_job_and_wait_state(UBUNTU_IMAGE_NAME, command)

    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(
            [
                "job",
                "exec",
                "--no-tty",
                "--no-key-check",
                "--timeout",
                str(EXEC_TIMEOUT),
                job_id,
            ]
        )
    assert cm.value.returncode == 2
    helper.kill_job(job_id, wait=False)


@pytest.mark.e2e
def test_e2e_ssh_exec_echo(helper: Helper) -> None:
    command = 'bash -c "sleep 15m; false"'
    job_id = helper.run_job_and_wait_state(UBUNTU_IMAGE_NAME, command)

    captured = helper.run_cli(
        [
            "job",
            "exec",
            "--no-tty",
            "--no-key-check",
            "--timeout",
            str(EXEC_TIMEOUT),
            job_id,
            "echo 1",
        ]
    )
    assert captured.out == "1"
    helper.kill_job(job_id, wait=False)


@pytest.mark.e2e
def test_e2e_ssh_exec_no_tty(helper: Helper) -> None:
    command = 'bash -c "sleep 15m; false"'
    job_id = helper.run_job_and_wait_state(UBUNTU_IMAGE_NAME, command)

    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(
            [
                "job",
                "exec",
                "--no-tty",
                "--no-key-check",
                "--timeout",
                str(EXEC_TIMEOUT),
                job_id,
                "[ -t 1 ]",
            ]
        )
    assert cm.value.returncode == 1
    helper.kill_job(job_id, wait=False)


@pytest.mark.e2e
def test_e2e_ssh_exec_tty(helper: Helper) -> None:
    command = 'bash -c "sleep 15m; false"'
    job_id = helper.run_job_and_wait_state(UBUNTU_IMAGE_NAME, command)

    captured = helper.run_cli(
        [
            "job",
            "exec",
            "--no-key-check",
            "--timeout",
            str(EXEC_TIMEOUT),
            job_id,
            "[ -t 1 ]",
        ]
    )
    assert captured.out == ""
    helper.kill_job(job_id, wait=False)


@pytest.mark.e2e
def test_e2e_ssh_exec_no_job(helper: Helper) -> None:
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(
            [
                "job",
                "exec",
                "--no-tty",
                "--no-key-check",
                "--timeout",
                str(EXEC_TIMEOUT),
                "job_id",
                "true",
            ]
        )
    assert cm.value.returncode == 127


@pytest.mark.e2e
def test_e2e_ssh_exec_dead_job(helper: Helper) -> None:
    command = "true"
    job_id = helper.run_job_and_wait_state(
        UBUNTU_IMAGE_NAME, command, wait_state=JobStatus.SUCCEEDED
    )

    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(
            [
                "job",
                "exec",
                "--no-tty",
                "--no-key-check",
                "--timeout",
                str(EXEC_TIMEOUT),
                job_id,
                "true",
            ]
        )
    assert cm.value.returncode == 127


@pytest.mark.e2e
def test_job_save(helper: Helper, docker: aiodocker.Docker) -> None:
    job_name = f"test-job-save-{uuid4().hex[:6]}"
    image = f"test-image:{job_name}"
    image_neuro_name = f"image://{helper.cluster_name}/{helper.username}/{image}"
    command = "sh -c 'echo -n 123 > /test; sleep 10m'"
    job_id_1 = helper.run_job_and_wait_state(
        ALPINE_IMAGE_NAME, command=command, wait_state=JobStatus.RUNNING
    )
    img_uri = f"image://{helper.cluster_name}/{helper.username}/{image}"
    captured = helper.run_cli(["job", "save", job_id_1, image_neuro_name])
    out = captured.out
    assert f"Saving job '{job_id_1}' to image '{img_uri}'..." in out
    assert f"Using remote image '{img_uri}'" in out
    assert "Creating image from the job container" in out
    assert "Image created" in out
    assert f"Using local image '{helper.username}/{image}'" in out
    assert "Pushing image..." in out
    assert out.endswith(img_uri)

    # wait to free the job name:
    helper.run_cli(["job", "kill", job_id_1])
    helper.wait_job_change_state_to(job_id_1, JobStatus.SUCCEEDED)

    command = 'sh -c \'[ "$(cat /test)" = "123" ]\''
    helper.run_job_and_wait_state(
        image_neuro_name, command=command, wait_state=JobStatus.SUCCEEDED
    )

    # TODO (A.Yushkovskiy): delete the pushed image in GCR


@pytest.fixture
async def nginx_job_async(
    nmrc_path: Path, loop: asyncio.AbstractEventLoop
) -> AsyncIterator[Tuple[str, str]]:
    async with api_get(path=nmrc_path) as client:
        secret = uuid4()
        command = (
            f"bash -c \"echo -n '{secret}' > /usr/share/nginx/html/secret.txt; "
            f"timeout 15m /usr/sbin/nginx -g 'daemon off;'\""
        )
        container = Container(
            image=RemoteImage.new_external_image(name="nginx", tag="latest"),
            command=command,
            resources=Resources(20, 0.1, None, None, True, None, None),
        )

        job = await client.jobs.run(
            container, is_preemptible=False, description="test NGINX job"
        )
        try:
            for i in range(60):
                status = await client.jobs.status(job.id)
                if status.status == JobStatus.RUNNING:
                    break
                await asyncio.sleep(1)
            else:
                raise AssertionError("Cannot start NGINX job")
            yield job.id, str(secret)
        finally:
            with suppress(Exception):
                await client.jobs.kill(job.id)


@pytest.mark.e2e
async def test_port_forward(nmrc_path: Path, nginx_job_async: Tuple[str, str]) -> None:
    loop_sleep = 1
    service_wait_time = 10 * 60

    async def get_(url: str) -> int:
        status = 999
        start_time = time()
        async with aiohttp.ClientSession() as session:
            while status != 200 and (int(time() - start_time) < service_wait_time):
                try:
                    async with session.get(url) as resp:
                        status = resp.status
                        text = await resp.text()
                        assert text == nginx_job_async[1], (
                            f"Secret not found "
                            f"via {url}. Like as it's not our test server."
                        )
                except aiohttp.ClientConnectionError:
                    status = 599
                if status != 200:
                    await asyncio.sleep(loop_sleep)
        return status

    async with api_get(path=nmrc_path, timeout=CLIENT_TIMEOUT) as client:
        port = unused_port()
        # We test client instead of run_cli as asyncio subprocesses do
        # not work if run from thread other than main.
        async with client.jobs.port_forward(
            nginx_job_async[0], port, 80, no_key_check=True
        ):
            await asyncio.sleep(loop_sleep)
            url = f"http://127.0.0.1:{port}/secret.txt"
            probe = await get_(url)
            assert probe == 200


@pytest.mark.e2e
def test_job_submit_http_auth(
    helper: Helper, secret_job: Callable[..., Dict[str, Any]]
) -> None:
    loop_sleep = 1
    service_wait_time = 10 * 60
    auth_url = helper.get_config()._config_data.auth_config.auth_url

    async def _test_http_auth_redirect(url: URL) -> None:
        start_time = time()
        async with aiohttp.ClientSession() as session:
            while time() - start_time < service_wait_time:
                try:
                    async with session.get(url, allow_redirects=True) as resp:
                        if resp.status == 200 and resp.url.host == auth_url.host:
                            break
                except aiohttp.ClientConnectionError:
                    pass
                await asyncio.sleep(loop_sleep)
            else:
                raise AssertionError("HTTP Auth not detected")

    async def _test_http_auth_with_cookie(
        url: URL, cookies: Dict[str, str], secret: str
    ) -> None:
        start_time = time()
        ntries = 0
        async with aiohttp.ClientSession(cookies=cookies) as session:  # type: ignore
            while time() - start_time < service_wait_time:
                try:
                    async with session.get(url, allow_redirects=False) as resp:
                        if resp.status == 200:
                            body = await resp.text()
                            if secret == body.strip():
                                break
                        ntries += 1
                        if ntries > 10:
                            raise AssertionError("Secret not match")
                except aiohttp.ClientConnectionError:
                    pass
                await asyncio.sleep(loop_sleep)
            else:
                raise AssertionError("Cannot fetch secret via forwarded http")

    http_job = secret_job(http_port=True, http_auth=True)
    ingress_secret_url = http_job["ingress_url"].with_path("/secret.txt")

    run(_test_http_auth_redirect(ingress_secret_url))

    cookies = {"dat": helper.token}
    run(_test_http_auth_with_cookie(ingress_secret_url, cookies, http_job["secret"]))


@pytest.mark.e2e
def test_job_run(helper: Helper) -> None:
    # Run a new job
    command = 'bash -c "exit 101"'
    captured = helper.run_cli(
        [
            "-q",
            "job",
            "run",
            "-s",
            JOB_TINY_CONTAINER_PRESET,
            "--no-wait-start",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    job_id = captured.out

    # Wait until the job is running
    helper.wait_job_change_state_to(job_id, JobStatus.FAILED)

    # Verify exit code is returned
    captured = helper.run_cli(["job", "status", job_id])
    store_out = captured.out
    assert "Exit code: 101" in store_out


@pytest.mark.e2e
def test_pass_config(helper: Helper) -> None:
    captured = helper.run_cli(
        [
            "-q",
            "job",
            "run",
            "-s",
            JOB_TINY_CONTAINER_PRESET,
            "--no-wait-start",
            "--pass-config",
            UBUNTU_IMAGE_NAME,
            'bash -c "sleep 15 && test -f $(NEURO_STEAL_CONFIG)/db"',
        ]
    )
    job_id = captured.out

    # fails if "test -f ..." check is not succeeded
    helper.wait_job_change_state_to(
        job_id, JobStatus.SUCCEEDED, stop_state=JobStatus.FAILED
    )


@pytest.mark.parametrize("http_auth", ["--http-auth", "--no-http-auth"])
@pytest.mark.e2e
def test_job_submit_bad_http_auth(helper: Helper, http_auth: str) -> None:
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(
            [
                "job",
                "submit",
                *JOB_TINY_CONTAINER_PARAMS,
                http_auth,
                "--no-wait-start",
                UBUNTU_IMAGE_NAME,
                "true",
            ]
        )
    assert cm.value.returncode == 2
    assert f"{http_auth} requires --http" in cm.value.stderr


@pytest.fixture
def fakebrowser(monkeypatch: Any) -> None:
    monkeypatch.setitem(os.environ, "BROWSER", "echo Browsing %s")


@pytest.mark.e2e
def test_job_browse(helper: Helper, fakebrowser: Any) -> None:
    # Run a new job
    captured = helper.run_cli(
        [
            "-q",
            "job",
            "run",
            "-s",
            JOB_TINY_CONTAINER_PRESET,
            "--detach",
            UBUNTU_IMAGE_NAME,
            "true",
        ]
    )
    job_id = captured.out

    captured = helper.run_cli(["-v", "job", "browse", job_id])
    assert "Browsing https://job-" in captured.out
    assert "Open job URL: https://job-" in captured.err


@pytest.mark.e2e
def test_job_run_browse(helper: Helper, fakebrowser: Any) -> None:
    # Run a new job
    captured = helper.run_cli(
        [
            "-v",
            "job",
            "run",
            "-s",
            JOB_TINY_CONTAINER_PRESET,
            "--detach",
            "--browse",
            UBUNTU_IMAGE_NAME,
            "true",
        ]
    )
    assert "Browsing https://job-" in captured.out
    assert "Open job URL: https://job-" in captured.err


@pytest.mark.e2e
def test_job_run_no_detach(helper: Helper) -> None:
    token = uuid4()
    # Run a new job
    captured = helper.run_cli(
        [
            "-v",
            "job",
            "run",
            "-s",
            JOB_TINY_CONTAINER_PRESET,
            UBUNTU_IMAGE_NAME,
            f"echo {token}",
        ]
    )
    assert str(token) in captured.out
    detach_notification = """\
Terminal is attached to the remote job, so you receive the job's output.
Use 'Ctrl-C' to detach (it will NOT terminate the job), or restart the job
with `--detach` option.\
"""
    assert detach_notification


@pytest.mark.e2e
def test_job_run_no_detach_quiet_mode(helper: Helper) -> None:
    token = str(uuid4())
    # Run a new job
    captured = helper.run_cli(
        [
            "-q",
            "job",
            "run",
            "-s",
            JOB_TINY_CONTAINER_PRESET,
            UBUNTU_IMAGE_NAME,
            f"echo {token}",
        ]
    )
    out = captured.out.strip()
    assert "Use 'Ctrl-C' to detach (it will NOT terminate the job)" not in out
    assert out.endswith(token)


@pytest.mark.e2e
def test_job_submit_no_detach_failure(helper: Helper) -> None:
    # Run a new job
    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        helper.run_cli(
            [
                "-v",
                "job",
                "submit",
                *JOB_TINY_CONTAINER_PARAMS,
                "--http",
                "80",
                UBUNTU_IMAGE_NAME,
                f"exit 127",
            ]
        )
    assert exc_info.value.returncode == 127


@pytest.mark.e2e
def test_job_run_no_detach_browse_failure(helper: Helper) -> None:
    # Run a new job
    captured = None
    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        captured = helper.run_cli(
            [
                "-v",
                "job",
                "run",
                "-s",
                JOB_TINY_CONTAINER_PRESET,
                "--detach",
                "--browse",
                UBUNTU_IMAGE_NAME,
                f"exit 123",
            ]
        )
    assert captured is None
    assert exc_info.value.returncode == 127


@pytest.mark.e2e
def test_job_run_with_tty(helper: Helper) -> None:
    # Run a new job
    command = "test -t 0"
    captured = helper.run_cli(
        [
            "-q",
            "job",
            "run",
            "-t",
            "-s",
            JOB_TINY_CONTAINER_PRESET,
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    job_id = captured.out

    # Wait until the job is running
    helper.wait_job_change_state_to(job_id, JobStatus.SUCCEEDED)

    captured = helper.run_cli(["job", "status", job_id])
    assert "TTY: True" in captured.out


@pytest.mark.e2e
def test_job_run_home_volumes_automount(helper: Helper, fakebrowser: Any) -> None:
    command = "[ -d /var/storage/home -a -d /var/storage/neuromation ]"

    with pytest.raises(subprocess.CalledProcessError) as cm:
        # first, run without --volume=HOME
        helper.run_cli(
            ["-q", "job", "run", "--preset=cpu-micro", UBUNTU_IMAGE_NAME, command]
        )

    assert cm.value.returncode == 1

    # then, run with --volume=HOME
    capture = helper.run_cli(
        [
            "-q",
            "job",
            "run",
            "--preset=cpu-micro",
            "--volume",
            "HOME",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )

    job_id_2 = capture.out
    helper.wait_job_change_state_to(job_id_2, JobStatus.SUCCEEDED, JobStatus.FAILED)


@pytest.mark.e2e
def test_job_run_volume_all(helper: Helper) -> None:
    root_mountpoint = "/var/neuro"
    cmd = " && ".join(
        [
            f"[ -d {root_mountpoint}/{helper.username} ]",
            f"[ -d {root_mountpoint}/neuromation ]",  # must be public
            f"[ -d {root_mountpoint}/test2/public ]",  # must be public
            f"[ $NEUROMATION_ROOT == {root_mountpoint} ]",
            f"[ $NEUROMATION_HOME == {root_mountpoint}/{helper.username} ]",
        ]
    )
    command = f"bash -c '{cmd}'"
    img = UBUNTU_IMAGE_NAME

    with pytest.raises(subprocess.CalledProcessError) as cm:
        # first, run without --volume=ALL
        captured = helper.run_cli(["--quiet", "run", "-s", "cpu-micro", img, command])
    assert cm.value.returncode == 1

    # then, run with --volume=ALL
    captured = helper.run_cli(["run", "-s", "cpu-micro", "--volume=ALL", img, command])
    msg = (
        "Storage mountpoints will be available as the environment variables:\n"
        f"  NEUROMATION_ROOT={root_mountpoint}\n"
        f"  NEUROMATION_HOME={root_mountpoint}/{helper.username}"
    )
    assert msg in captured.out
    found_job_ids = re.findall("Job ID: (job-.+) Status:", captured.out)
    assert len(found_job_ids) == 1
    job_id = found_job_ids[0]
    helper.wait_job_change_state_to(
        job_id, JobStatus.SUCCEEDED, stop_state=JobStatus.FAILED
    )


@pytest.mark.e2e
def test_job_run_volume_all_and_home(helper: Helper) -> None:
    with pytest.raises(subprocess.CalledProcessError):
        args = ["--volume", "ALL", "--volume", "HOME"]
        captured = helper.run_cli(["job", "run", *args, UBUNTU_IMAGE_NAME, "sleep 30"])
        msg = "Cannot use `--volume=ALL` together with other `--volume` options"
        assert msg in captured.err


@pytest.mark.e2e
def test_job_run_volume_all_and_another(helper: Helper) -> None:
    with pytest.raises(subprocess.CalledProcessError):
        args = ["--volume", "ALL", "--volume", "storage::/home:ro"]
        captured = helper.run_cli(["job", "run", *args, UBUNTU_IMAGE_NAME, "sleep 30"])
        msg = "Cannot use `--volume=ALL` together with other `--volume` options"
        assert msg in captured.err


@pytest.mark.e2e
def test_e2e_job_top(helper: Helper) -> None:
    def split_non_empty_parts(line: str, sep: str) -> List[str]:
        return [part.strip() for part in line.split(sep) if part.strip()]

    command = f"sleep 300"

    print("Run job... ")
    job_id = helper.run_job_and_wait_state(image=UBUNTU_IMAGE_NAME, command=command)
    print("... done")
    t0 = time()
    returncode = -1
    delay = 15.0

    while returncode and time() - t0 < 3 * 60:
        try:
            print("Try job top")
            capture = helper.run_cli(["job", "top", job_id, "--timeout", str(delay)])
        except subprocess.CalledProcessError as ex:
            stdout = ex.output
            stderr = ex.stderr
            returncode = ex.returncode
        else:
            stdout = capture.out
            stderr = capture.err
            returncode = 0

        if "TIMESTAMP" in stdout and "MEMORY (MB)" in stdout:
            # got response from job top telemetery
            returncode = 0
            break
        else:
            print(f"job top has failed, increase timeout to {delay}")
            delay = min(delay * 1.5, 60)

    # timeout is reached without info from server
    assert not returncode, (
        f"Cannot get response from server "
        f"in {time() - t0} secs, delay={delay} "
        f"returncode={returncode}\n"
        f"stdout = {stdout}\nstdderr = {stderr}"
    )

    helper.kill_job(job_id, wait=False)

    try:
        header, *lines = split_non_empty_parts(stdout, sep="\n")
    except ValueError:
        assert False, f"cannot unpack\n{stdout}\n{stderr}"
    header_parts = split_non_empty_parts(header, sep="\t")
    assert header_parts == [
        "TIMESTAMP",
        "CPU",
        "MEMORY (MB)",
        "GPU (%)",
        "GPU_MEMORY (MB)",
    ]

    for line in lines:
        line_parts = split_non_empty_parts(line, sep="\t")
        timestamp_pattern_parts = [
            ("weekday", "[A-Z][a-z][a-z]"),
            ("month", "[A-Z][a-z][a-z]"),
            ("day", r"\d+"),
            ("day", r"\d\d:\d\d:\d\d"),
            ("year", r"\d{4}"),
        ]
        timestamp_pattern = r"\s+".join([part[1] for part in timestamp_pattern_parts])
        expected_parts = [
            ("timestamp", timestamp_pattern),
            ("cpu", r"\d.\d\d\d"),
            ("memory", r"\d.\d\d\d"),
            ("gpu", "0"),
            ("gpu memory", "0"),
        ]
        for actual, (descr, pattern) in zip(line_parts, expected_parts):
            assert re.match(pattern, actual) is not None, f"error in matching {descr}"


@pytest.mark.e2e
def test_e2e_restart_failing(request: Any, helper: Helper) -> None:
    captured = helper.run_cli(
        [
            "-q",
            "job",
            "run",
            "--restart",
            "on-failure",
            "-s",
            JOB_TINY_CONTAINER_PRESET,
            "--detach",
            UBUNTU_IMAGE_NAME,
            "false",
        ]
    )
    job_id = captured.out
    request.addfinalizer(lambda: helper.kill_job(job_id, wait=False))

    captured = helper.run_cli(["job", "status", job_id])
    assert "Restart policy: on-failure" in captured.out.splitlines()

    helper.wait_job_change_state_to(job_id, JobStatus.RUNNING)
    sleep(1)
    helper.assert_job_state(job_id, JobStatus.RUNNING)


@pytest.mark.skipif(
    sys.platform == "win32", reason="Autocompletion is not supported on Windows"
)
@pytest.mark.e2e
def test_job_autocomplete(helper: Helper) -> None:

    job_name = f"test-job-{os.urandom(5).hex()}"
    helper.kill_job(job_name)
    job_id = helper.run_job_and_wait_state(ALPINE_IMAGE_NAME, "sleep 60", name=job_name)

    out = helper.autocomplete(["kill", "test-job"])
    assert job_name in out
    assert job_id not in out

    out = helper.autocomplete(["kill", "job-"])
    assert job_name in out
    assert job_id in out

    out = helper.autocomplete(["kill", "job:job-"])
    assert job_name in out
    assert job_id in out

    out = helper.autocomplete(["kill", f"job:/{helper.username}/job-"])
    assert job_name in out
    assert job_id in out

    out = helper.autocomplete(
        ["kill", f"job://{helper.cluster_name}/{helper.username}/job-"]
    )
    assert job_name in out
    assert job_id in out

    helper.kill_job(job_id)
