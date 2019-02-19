import re
from uuid import uuid4 as uuid

import aiohttp
import pytest

from tests.e2e.test_e2e_utils import (
    Status,
    wait_job_change_state_from,
    wait_job_change_state_to,
)


NGINX_IMAGE_NAME = "nginx:latest"
UBUNTU_IMAGE_NAME = "ubuntu:latest"
ALPINE_IMAGE_NAME = "alpine:latest"


@pytest.fixture
def run_job_and_wait_status(run):
    def go(image, command, params):
        captured = run(
            ["job", "submit"] + params + ([image, command] if command else [image])
        )

        assert not captured.err
        job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)
        wait_job_change_state_from(run, job_id, Status.PENDING, Status.FAILED)
        return job_id

    return go


@pytest.fixture()
def tiny_container():
    return ["-m", "20M", "-c", "0.1", "-g", "0", "--non-preemptible"]


@pytest.fixture
def secret_job(run_job_and_wait_status, tiny_container, run):
    def go(http_port: bool):
        secret = str(uuid())
        # Run http job
        command = (
            f"bash -c \"echo '{secret}' > /usr/share/nginx/html/secret.txt; "
            f"timeout 5m /usr/sbin/nginx -g 'daemon off;'\""
        )
        if http_port:
            args = ["--http", "80", "-d", "nginx with secret file and http port"]
        else:
            args = ["-d", "nginx with secret file and without http port"]

        http_job_id = run_job_and_wait_status(
            NGINX_IMAGE_NAME, command, tiny_container + args
        )
        captured = run(["job", "status", http_job_id])
        match_ingress_url = re.search(r"Http URL:\s+(\S+)", captured.out)
        if match_ingress_url:
            ingress_url = match_ingress_url.group(1)
        else:
            ingress_url = None
        internal_hostname = re.search(
            r"Internal Hostname:\s+(\S+)", captured.out
        ).group(1)

        return {
            "id": http_job_id,
            "secret": secret,
            "ingress_url": ingress_url,
            "internal_hostname": internal_hostname,
        }

    return go


@pytest.mark.e2e
def test_connectivity_job_with_http_port(
    run,
    secret_job,
    run_job_and_wait_status,
    check_http_get,
    tiny_container,
    check_job_output,
):

    http_job = secret_job(True)

    ingress_secret_url = f"{http_job['ingress_url']}/secret.txt"

    # external ingress test
    probe = check_http_get(ingress_secret_url)
    assert probe.strip() == http_job["secret"]

    # internal ingress test
    command = f"wget -q {ingress_secret_url} -O -"
    job_id = run_job_and_wait_status(
        ALPINE_IMAGE_NAME, command, tiny_container + ["-d", "secret ingress fetcher "]
    )
    wait_job_change_state_to(run, job_id, Status.SUCCEEDED, Status.FAILED)
    check_job_output(job_id, http_job["secret"])

    # internal network test
    internal_secret_url = f"http://{http_job['internal_hostname']}/secret.txt"
    command = f"wget -q {internal_secret_url} -O -"
    job_id = run_job_and_wait_status(
        ALPINE_IMAGE_NAME,
        command,
        tiny_container + ["-d", "secret internal network fetcher "],
    )
    wait_job_change_state_to(run, job_id, Status.SUCCEEDED, Status.FAILED)
    check_job_output(job_id, http_job["secret"])


@pytest.mark.e2e
def test_connectivity_job_without_http_port(
    run, secret_job, check_http_get, tiny_container, check_job_output
):
    # run http job for getting url
    http_job = secret_job(True)
    run(["job", "kill", http_job["id"]])
    ingress_secret_url = f"{http_job['ingress_url']}/secret.txt"

    # Run another job without shared http port
    no_http_job = secret_job(False)

    # Let's emulate external url
    ingress_secret_url = ingress_secret_url.replace(http_job["id"], no_http_job["id"])

    # external ingress test
    # it will take ~2 min, because we need to wait while nginx started
    with pytest.raises(aiohttp.ClientResponseError):
        check_http_get(ingress_secret_url)

    # internal ingress test
    command = f"wget -q {ingress_secret_url} -O -"
    captured = run(
        ["job", "submit"]
        + tiny_container
        + ["-d", "secret ingress fetcher "]
        + [ALPINE_IMAGE_NAME, command]
    )
    assert not captured.err
    job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)
    wait_job_change_state_to(run, job_id, Status.FAILED, Status.SUCCEEDED)
    check_job_output(job_id, r"wget.+404.+Not Found")

    # internal network test
    # cannot be implemented now
    # because by default k8s will not register DNS name if pod
    # haven't any service


@pytest.mark.e2e
@pytest.mark.xfail
def test_check_isolation(
    run,
    secret_job,
    run_job_and_wait_status,
    tiny_container,
    switch_user,
    check_job_output,
):
    http_job = secret_job(True)

    ingress_secret_url = f"{http_job['ingress_url']}/secret.txt"

    switch_user()

    # internal ingress test
    command = f"wget -q {ingress_secret_url} -O -"
    job_id = run_job_and_wait_status(
        ALPINE_IMAGE_NAME,
        command,
        tiny_container + ["-d", "alt secret ingress fetcher "],
    )
    wait_job_change_state_to(run, job_id, Status.SUCCEEDED, Status.FAILED)
    check_job_output(job_id, http_job["secret"])

    # internal network test
    internal_secret_url = f"http://{http_job['internal_hostname']}/secret.txt"
    command = f"wget -q {internal_secret_url} -O -"
    job_id = run_job_and_wait_status(
        ALPINE_IMAGE_NAME, command, tiny_container + ["-d", "secret network fetcher "]
    )
    # This job must be failed,
    # wget must return error. something like "Connection refused"
    # but we have problem at this moment
    # TODO check next lines when problem will fixed
    wait_job_change_state_to(run, job_id, Status.FAILED, Status.SUCCEEDED)
    # With some unknown status
    check_job_output(job_id, r"Connection refused")
