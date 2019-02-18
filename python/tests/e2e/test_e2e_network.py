import re
from uuid import uuid4 as uuid

import aiohttp
import pytest

from tests.e2e.test_e2e_utils import (
    Status,
    wait_job_change_state_from,
    wait_job_change_state_to,
)
from tests.e2e.utils import attempt


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
        return http_job_id, secret

    return go


@pytest.mark.e2e
def test_connectivity(
    run, secret_job, run_job_and_wait_status, check_http_get, tiny_container
):

    http_job_id, secret = secret_job(True)

    captured = run(["job", "status", http_job_id])
    ingress_url = re.search(r"Http URL:\s+(\S+)", captured.out).group(1)

    secret_url = ingress_url + "/secret.txt"

    # external ingress test
    probe = check_http_get(secret_url)
    assert probe.strip() == secret

    # internal ingress test
    command = f"wget -q {secret_url} -O -"
    job_id = run_job_and_wait_status(
        ALPINE_IMAGE_NAME, command, tiny_container + ["-d", "secret ingress fetcher "]
    )
    wait_job_change_state_to(run, job_id, Status.SUCCEEDED, Status.FAILED)
    captured = run(["job", "logs", job_id])
    assert not captured.err
    assert captured.out == secret

    # internal network test
    captured = run(["job", "status", http_job_id])
    assert not captured.err
    internal_hostname = re.search(r"Internal Hostname:\s+(\S+)", captured.out).group(1)
    internal_secret_url = f"http://{internal_hostname}/secret.txt"
    command = f"wget -q {internal_secret_url} -O -"
    job_id = run_job_and_wait_status(
        ALPINE_IMAGE_NAME, command, tiny_container + ["-d", "secret network fetcher "]
    )
    wait_job_change_state_to(run, job_id, Status.SUCCEEDED, Status.FAILED)

    @attempt()
    def check_internal_test_job_output():
        captured = run(["job", "logs", job_id])
        assert not captured.err
        assert captured.out == secret

    check_internal_test_job_output()

    # let's kill unused http job
    run(["job", "kill", job_id])

    # Run another job without shared http port
    no_http_job_id, secret = secret_job(False)

    # Let's emulate external url
    secret_url = secret_url.replace(http_job_id, no_http_job_id)

    #  external ingress test
    #  it will take ~2 min, because we will wait while nginx started
    with pytest.raises(aiohttp.ClientResponseError):
        check_http_get(secret_url)

    # internal ingress test
    command = f"wget -q {secret_url} -O -"
    captured = run(
        ["job", "submit"]
        + tiny_container
        + ["-d", "secret ingress fetcher "]
        + [ALPINE_IMAGE_NAME, command]
    )
    assert not captured.err
    job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)
    wait_job_change_state_to(run, job_id, Status.FAILED, Status.SUCCEEDED)

    @attempt()
    def check_no_http_internal_test_job_output():
        captured = run(["job", "logs", job_id])
        assert not captured.err
        assert re.search(r"wget.+404.+Not Found", captured.out) is not None

    check_no_http_internal_test_job_output()

    # internal network test
    # code below commented from 18/02/2019
    # because by default k8s will not register DNS name if pod
    # haven't any service
    # TODO uncomment next part if behavior changed

    # captured = run(["job", "status", no_http_job_ id])
    # assert not captured.err
    # internal_hostname = \
    # re.search(r"Internal Hostname:\s+(\S+)", captured.out).group(1)
    # internal_secret_url = f"http://{internal_hostname}/secret.txt"
    # command = f"wget -q {internal_secret_url} -O -"
    # job_id = run_job_and_wait_status(
    #     ALPINE_IMAGE_NAME, command, tiny_container + ["-d", "secret network fetcher "]
    # )
    # wait_job_change_state_to(run, job_id, Status.SUCCEEDED, Status.FAILED)
    # captured = run(["job", "logs", job_id])
    # assert not captured.err
    # assert captured.out == secret
    # let's kill unused http job

    run(["job", "kill", no_http_job_id])
