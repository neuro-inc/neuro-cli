import os
import re
from time import sleep, time
from urllib.parse import urlparse

import aiohttp
import pytest

from neuromation.cli.rc import ConfigFactory
from neuromation.utils import run as run_async
from tests.e2e.test_e2e_utils import (
    Status,
    assert_job_state,
    wait_job_change_state_from,
    wait_job_change_state_to,
)


UBUNTU_IMAGE_NAME = "ubuntu:latest"
NGINX_IMAGE_NAME = "nginx:latest"


@pytest.mark.e2e
def test_job_lifecycle(run):
    # Remember original running jobs
    captured = run(["job", "list", "--status", "running,pending"])
    store_out_list = captured.out.strip().split("\n")[1:]
    jobs_orig = [x.split("\t")[0] for x in store_out_list]

    # Run a new job
    command = 'bash -c "sleep 10m; false"'
    captured = run(
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
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)

    # Check it was not running before
    assert job_id.startswith("job-")
    assert job_id not in jobs_orig

    # Check it is in a running,pending job list now
    captured = run(["job", "list", "--status", "running,pending"])
    store_out_list = captured.out.strip().split("\n")[1:]
    jobs_updated = [x.split("\t")[0] for x in store_out_list]
    assert job_id in jobs_updated

    # Wait until the job is running
    wait_job_change_state_to(run, job_id, Status.RUNNING)

    # Check that it is in a running job list
    captured = run(["job", "list", "--status", "running"])
    store_out = captured.out.strip()
    assert job_id in store_out
    # Check that the command is in the list
    assert command in store_out

    # Check that no command is in the list if quite
    captured = run(["job", "list", "--status", "running", "-q"])
    store_out = captured.out.strip()
    assert job_id in store_out
    assert command not in store_out

    # Kill the job
    captured = run(["job", "kill", job_id])

    # Check that the job we killed ends up as succeeded
    wait_job_change_state_to(run, job_id, Status.SUCCEEDED)

    # Check that it is not in a running job list anymore
    captured = run(["job", "list", "--status", "running"])
    store_out = captured.out.strip()
    assert job_id not in store_out


@pytest.mark.e2e
def test_job_description(run):
    # Remember original running jobs
    captured = run(["job", "list", "--status", "running,pending"])
    store_out_list = captured.out.strip().split("\n")[1:]
    jobs_orig = [x.split("\t")[0] for x in store_out_list]
    description = "Test description for a job"
    # Run a new job
    command = 'bash -c "sleep 10m; false"'
    captured = run(
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
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)

    # Check it was not running before
    assert job_id.startswith("job-")
    assert job_id not in jobs_orig

    # Check it is in a running,pending job list now
    captured = run(["job", "list", "--status", "running,pending"])
    store_out_list = captured.out.strip().split("\n")[1:]
    jobs_updated = [x.split("\t")[0] for x in store_out_list]
    assert job_id in jobs_updated

    # Wait until the job is running
    wait_job_change_state_to(run, job_id, Status.RUNNING)

    # Check that it is in a running job list
    captured = run(["job", "list", "--status", "running"])
    store_out = captured.out.strip()
    assert job_id in store_out
    # Check that description is in the list
    assert description in store_out
    assert command in store_out

    # Check that no description is in the list if quite
    captured = run(["job", "list", "--status", "running", "-q"])
    store_out = captured.out.strip()
    assert job_id in store_out
    assert description not in store_out
    assert command not in store_out

    # Kill the job
    captured = run(["job", "kill", job_id])

    # Check that the job we killed ends up as succeeded
    wait_job_change_state_to(run, job_id, Status.SUCCEEDED)

    # Check that it is not in a running job list anymore
    captured = run(["job", "list", "--status", "running"])
    store_out = captured.out.strip()
    assert job_id not in store_out


@pytest.mark.e2e
def test_unschedulable_job_lifecycle(run):
    # Remember original running jobs
    captured = run(["job", "list", "--status", "running,pending"])
    store_out_list = captured.out.strip().split("\n")[1:]
    jobs_orig = [x.split("\t")[0] for x in store_out_list]

    # Run a new job
    command = 'bash -c "sleep 10m; false"'
    captured = run(
        [
            "job",
            "submit",
            "-m",
            "20000000M",
            "-c",
            "0.1",
            "-g",
            "0",
            "--http",
            "80",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)

    # Check it was not running before
    assert job_id.startswith("job-")
    assert job_id not in jobs_orig

    # Check it is in a running,pending job list now
    captured = run(["job", "list", "--status", "running,pending"])
    store_out_list = captured.out.strip().split("\n")[1:]
    jobs_updated = [x.split("\t")[0] for x in store_out_list]
    assert job_id in jobs_updated

    # Kill the job
    captured = run(["job", "kill", job_id])

    # Check that the job we killed ends up as succeeded
    wait_job_change_state_to(run, job_id, Status.SUCCEEDED)

    # Check that it is not in a running job list anymore
    captured = run(["job", "list", "--status", "running"])
    store_out = captured.out.strip()
    assert job_id not in store_out


@pytest.mark.e2e
def test_two_jobs_at_once(run):
    # Remember original running jobs
    captured = run(["job", "list", "--status", "running,pending"])
    store_out_list = captured.out.strip().split("\n")[1:]
    jobs_orig = [x.split("\t")[0] for x in store_out_list]

    # Run a new job
    command = 'bash -c "sleep 10m; false"'
    captured = run(
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
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    first_job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)

    captured = run(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "-g",
            "0",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )
    second_job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)

    # Check it was not running before
    assert first_job_id.startswith("job-")
    assert first_job_id not in jobs_orig
    assert second_job_id.startswith("job-")
    assert second_job_id not in jobs_orig

    # Check it is in a running,pending job list now
    captured = run(["job", "list", "--status", "running,pending"])
    store_out_list = captured.out.strip().split("\n")[1:]
    jobs_updated = [x.split("\t")[0] for x in store_out_list]
    assert first_job_id in jobs_updated
    assert second_job_id in jobs_updated

    # Wait until the job is running
    wait_job_change_state_to(run, first_job_id, Status.RUNNING)
    wait_job_change_state_to(run, second_job_id, Status.RUNNING)

    # Check that it is in a running job list
    captured = run(["job", "list", "--status", "running"])
    store_out = captured.out.strip()
    assert first_job_id in store_out
    assert second_job_id in store_out
    # Check that the command is in the list
    assert command in store_out

    # Check that no command is in the list if quite
    captured = run(["job", "list", "--status", "running", "-q"])
    store_out = captured.out.strip()
    assert first_job_id in store_out
    assert second_job_id in store_out
    assert command not in store_out

    # Kill the job
    captured = run(["job", "kill", first_job_id, second_job_id])

    # Check that the job we killed ends up as succeeded
    wait_job_change_state_to(run, first_job_id, Status.SUCCEEDED)
    wait_job_change_state_to(run, second_job_id, Status.SUCCEEDED)

    # Check that it is not in a running job list anymore
    captured = run(["job", "list", "--status", "running"])
    store_out = captured.out.strip()
    assert first_job_id not in store_out
    assert first_job_id not in store_out


@pytest.mark.e2e
def test_job_kill_non_existing(run):
    # try to kill non existing job
    phantom_id = "NOT_A_JOB_ID"
    expected_out = f"Cannot kill job {phantom_id}"
    captured = run(["job", "kill", phantom_id])
    killed_jobs = [x.strip() for x in captured.out.strip().split("\n")]
    assert len(killed_jobs) == 1
    assert killed_jobs[0].startswith(expected_out)


@pytest.mark.e2e
def test_model_train_with_http(run, tmpstorage, check_create_dir_on_storage):
    loop_sleep = 1
    service_wait_time = 60

    async def get_(platform_url):
        succeeded = None
        start_time = time()
        while not succeeded and (int(time() - start_time) < service_wait_time):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://{job_id}.jobs.{platform_url}") as resp:
                    succeeded = resp.status == 200
            if not succeeded:
                sleep(loop_sleep)
        return succeeded

    # Create directory for the test, going to be model and result output
    check_create_dir_on_storage("model")
    check_create_dir_on_storage("result")

    # Start the job
    command = '/usr/sbin/nginx -g "daemon off;"'
    captured = run(
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
            f"{tmpstorage}/model",
            f"{tmpstorage}/result",
            command,
        ]
    )
    job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)
    wait_job_change_state_from(run, job_id, Status.PENDING)

    config = ConfigFactory.load()
    parsed_url = urlparse(config.url)

    assert run_async(get_(parsed_url.netloc))

    run(["job", "kill", job_id])
    wait_job_change_state_from(run, job_id, Status.RUNNING)


@pytest.mark.e2e
def test_model_without_command(run, tmpstorage, check_create_dir_on_storage):
    loop_sleep = 1
    service_wait_time = 60

    async def get_(platform_url):
        succeeded = None
        start_time = time()
        while not succeeded and (int(time() - start_time) < service_wait_time):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://{job_id}.jobs.{platform_url}") as resp:
                    succeeded = resp.status == 200
            if not succeeded:
                sleep(loop_sleep)
        return succeeded

    # Create directory for the test, going to be model and result output
    check_create_dir_on_storage("model")
    check_create_dir_on_storage("result")

    # Start the job
    captured = run(
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
            f"{tmpstorage}/model",
            f"{tmpstorage}/result",
            "-d",
            "simple test job",
        ]
    )
    job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)
    wait_job_change_state_from(run, job_id, Status.PENDING)

    config = ConfigFactory.load()
    parsed_url = urlparse(config.url)

    assert run_async(get_(parsed_url.netloc))

    captured = run(["job", "kill", job_id])
    wait_job_change_state_from(run, job_id, Status.RUNNING)


@pytest.mark.e2e
def test_e2e_no_env(run):
    bash_script = 'echo "begin"$VAR"end"  | grep beginend'
    command = f"bash -c '{bash_script}'"
    captured = run(
        [
            "job",
            "submit",
            "-m",
            "20M",
            "-c",
            "0.1",
            "-g",
            "0",
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )

    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    wait_job_change_state_from(run, job_id, Status.PENDING)
    wait_job_change_state_from(run, job_id, Status.RUNNING)

    assert_job_state(run, job_id, "Status: succeeded")


@pytest.mark.e2e
def test_e2e_env(run):
    bash_script = 'echo "begin"$VAR"end"  | grep beginVALend'
    command = f"bash -c '{bash_script}'"
    captured = run(
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
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )

    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    wait_job_change_state_from(run, job_id, Status.PENDING)
    wait_job_change_state_from(run, job_id, Status.RUNNING)

    assert_job_state(run, job_id, "Status: succeeded")


@pytest.mark.e2e
def test_e2e_env_from_local(run):
    os.environ["VAR"] = "VAL"
    bash_script = 'echo "begin"$VAR"end"  | grep beginVALend'
    command = f"bash -c '{bash_script}'"
    captured = run(
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
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )

    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    wait_job_change_state_from(run, job_id, Status.PENDING)
    wait_job_change_state_from(run, job_id, Status.RUNNING)

    assert_job_state(run, job_id, "Status: succeeded")


@pytest.mark.e2e
def test_e2e_multiple_env(run):
    bash_script = 'echo begin"$VAR""$VAR2"end  | grep beginVALVAL2end'
    command = f"bash -c '{bash_script}'"
    captured = run(
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
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )

    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    wait_job_change_state_from(run, job_id, Status.PENDING)
    wait_job_change_state_from(run, job_id, Status.RUNNING)

    assert_job_state(run, job_id, "Status: succeeded")


@pytest.mark.e2e
def test_e2e_multiple_env_from_file(run, tmp_path):
    env_file = tmp_path / "env_file"
    env_file.write_text("VAR2=LAV2\nVAR3=VAL3\n")
    bash_script = 'echo begin"$VAR""$VAR2""$VAR3"end  | grep beginVALVAL2VAL3end'
    command = f"bash -c '{bash_script}'"
    captured = run(
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
            UBUNTU_IMAGE_NAME,
            command,
        ]
    )

    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    wait_job_change_state_from(run, job_id, Status.PENDING)
    wait_job_change_state_from(run, job_id, Status.RUNNING)

    assert_job_state(run, job_id, "Status: succeeded")


@pytest.mark.e2e
def test_e2e_ssh_exec_true(run):
    command = 'bash -c "sleep 1m; false"'
    captured = run(
        ["job", "submit", "-m", "20M", "-c", "0.1", UBUNTU_IMAGE_NAME, command]
    )
    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    wait_job_change_state_to(run, job_id, Status.RUNNING)

    captured = run(["job", "exec", "--no-key-check", job_id, "true"])
    assert captured.out == ""


@pytest.mark.e2e
def test_e2e_ssh_exec_false(run):
    command = 'bash -c "sleep 1m; false"'
    captured = run(
        ["job", "submit", "-m", "20M", "-c", "0.1", UBUNTU_IMAGE_NAME, command]
    )
    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    wait_job_change_state_to(run, job_id, Status.RUNNING)

    with pytest.raises(SystemExit) as cm:
        run(["job", "exec", "--no-key-check", job_id, "false"])
    assert cm.value.code == 1


@pytest.mark.e2e
def test_e2e_ssh_exec_echo(run):
    command = 'bash -c "sleep 1m; false"'
    captured = run(
        ["job", "submit", "-m", "20M", "-c", "0.1", UBUNTU_IMAGE_NAME, command]
    )
    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    wait_job_change_state_to(run, job_id, Status.RUNNING)

    captured = run(["job", "exec", "--no-key-check", job_id, "echo 1"])
    assert captured.out == "1\n"


@pytest.mark.e2e
def test_e2e_ssh_exec_no_tty(run):
    command = 'bash -c "sleep 1m; false"'
    captured = run(
        ["job", "submit", "-m", "20M", "-c", "0.1", UBUNTU_IMAGE_NAME, command]
    )
    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    wait_job_change_state_to(run, job_id, Status.RUNNING)

    with pytest.raises(SystemExit) as cm:
        run(["job", "exec", "--no-key-check", job_id, "[ -t 1 ]"])
    assert cm.value.code == 1


@pytest.mark.e2e
def test_e2e_ssh_exec_tty(run):
    command = 'bash -c "sleep 1m; false"'
    captured = run(
        ["job", "submit", "-m", "20M", "-c", "0.1", UBUNTU_IMAGE_NAME, command]
    )
    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    wait_job_change_state_to(run, job_id, Status.RUNNING)

    captured = run(["job", "exec", "-t", "--no-key-check", job_id, "[ -t 1 ]"])
    assert captured.out == ""


@pytest.mark.e2e
def test_e2e_ssh_exec_no_job(run):
    with pytest.raises(SystemExit) as cm:
        run(["job", "exec", "--no-key-check", "job_id", "true"])
    assert cm.value.code == 127


@pytest.mark.e2e
def test_e2e_ssh_exec_dead_job(run):
    command = "true"
    captured = run(
        ["job", "submit", "-m", "20M", "-c", "0.1", UBUNTU_IMAGE_NAME, command]
    )
    out = captured.out
    job_id = re.match("Job ID: (.+) Status:", out).group(1)

    wait_job_change_state_from(run, job_id, Status.PENDING)
    wait_job_change_state_from(run, job_id, Status.RUNNING)

    with pytest.raises(SystemExit) as cm:
        run(["job", "exec", "--no-key-check", job_id, "true"])
    assert cm.value.code == 127
