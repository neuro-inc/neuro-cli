import re
from uuid import uuid4 as uuid

import aiohttp
import pytest

from neuromation.client import JobDescription, JobStatus
from tests.e2e.utils import JOB_TINY_CONTAINER_PARAMS


NGINX_IMAGE_NAME = "nginx:latest"
UBUNTU_IMAGE_NAME = "ubuntu:latest"
ALPINE_IMAGE_NAME = "alpine:latest"


@pytest.fixture
def secret_job(helper):
    def go(http_port: bool):
        secret = str(uuid())
        # Run http job
        command = (
            f"bash -c \"echo '{secret}' > /usr/share/nginx/html/secret.txt; "
            f"timeout 15m /usr/sbin/nginx -g 'daemon off;'\""
        )
        if http_port:
            args = ["--http", "80", "-d", "nginx with secret file and http port"]
        else:
            args = ["-d", "nginx with secret file and without http port"]

        http_job_id = helper.run_job_and_wait_state(
            NGINX_IMAGE_NAME, command, JOB_TINY_CONTAINER_PARAMS + args
        )
        status: JobDescription = helper.job_info(http_job_id)
        return {
            "id": http_job_id,
            "secret": secret,
            "ingress_url": status.http_url,
            "internal_hostname": status.internal_hostname,
        }

    return go


@pytest.mark.e2e
@pytest.mark.no_win32
def test_connectivity_job_with_http_port(secret_job, helper):

    http_job = secret_job(True)

    ingress_secret_url = http_job["ingress_url"].with_path("/secret.txt")

    # external ingress test
    probe = helper.check_http_get(ingress_secret_url)
    assert probe
    assert probe.strip() == http_job["secret"]

    # internal ingress test
    command = f"wget -q -T 15 {ingress_secret_url} -O -"
    job_id = helper.run_job_and_wait_state(
        ALPINE_IMAGE_NAME,
        command,
        JOB_TINY_CONTAINER_PARAMS + ["-d", "secret ingress fetcher "],
        wait_state=JobStatus.SUCCEEDED,
    )
    helper.check_job_output(job_id, re.escape(http_job["secret"]))

    # internal network test
    internal_secret_url = f"http://{http_job['internal_hostname']}/secret.txt"
    command = f"wget -q -T 15 {internal_secret_url} -O -"
    job_id = helper.run_job_and_wait_state(
        ALPINE_IMAGE_NAME,
        command,
        JOB_TINY_CONTAINER_PARAMS + ["-d", "secret internal network fetcher "],
        wait_state=JobStatus.SUCCEEDED,
    )
    helper.check_job_output(job_id, re.escape(http_job["secret"]))


@pytest.mark.e2e
@pytest.mark.no_win32
def test_connectivity_job_without_http_port(secret_job, helper):
    # run http job for getting url
    http_job = secret_job(True)
    helper.run_cli(["job", "kill", http_job["id"]])
    ingress_secret_url = http_job["ingress_url"].with_path("/secret.txt")

    # Run another job without shared http port
    no_http_job = secret_job(False)

    # Let's emulate external url
    ingress_secret_url = str(ingress_secret_url).replace(
        http_job["id"], no_http_job["id"]
    )

    # external ingress test
    # it will take ~1 min, because we need to wait while nginx started
    with pytest.raises(aiohttp.ClientResponseError):
        helper.check_http_get(ingress_secret_url)

    # internal ingress test
    command = f"wget -q -T 15 {ingress_secret_url} -O -"
    job_id = helper.run_job_and_wait_state(
        ALPINE_IMAGE_NAME,
        command,
        JOB_TINY_CONTAINER_PARAMS + ["-d", "secret ingress fetcher "],
        wait_state=JobStatus.FAILED,
        stop_state=JobStatus.SUCCEEDED,
    )
    helper.check_job_output(job_id, r"wget.+404.+Not Found")

    # internal network test
    # cannot be implemented now
    # because by default k8s will not register DNS name if pod
    # haven't any service
    # internal network test


@pytest.mark.e2e
@pytest.mark.no_win32
def test_check_isolation(secret_job, helper_alt):
    http_job = secret_job(True)

    ingress_secret_url = f"{http_job['ingress_url']}/secret.txt"

    # internal ingress test
    command = f"wget -q -T 15 {ingress_secret_url} -O -"
    job_id = helper_alt.run_job_and_wait_state(
        ALPINE_IMAGE_NAME,
        command,
        JOB_TINY_CONTAINER_PARAMS + ["-d", "secret ingress fetcher "],
        wait_state=JobStatus.SUCCEEDED,
    )
    helper_alt.check_job_output(job_id, re.escape(http_job["secret"]))

    # internal network test

    internal_secret_url = f"http://{http_job['internal_hostname']}/secret.txt"
    command = f"wget -q -T 15 {internal_secret_url} -O -"
    # This job must be failed,
    job_id = helper_alt.run_job_and_wait_state(
        ALPINE_IMAGE_NAME,
        command,
        JOB_TINY_CONTAINER_PARAMS + ["-d", "secret internal network fetcher "],
        wait_state=JobStatus.FAILED,
        stop_state=JobStatus.SUCCEEDED,
    )
    helper_alt.check_job_output(job_id, r"timed out")
