import re
from uuid import uuid4 as uuid


from tests.e2e.test_e2e_utils import (
    Status,
    wait_job_change_state_from,
    wait_job_change_state_to
)

NGINX_IMAGE_NAME = "nginx:latest"
UBUNTU_IMAGE_NAME = "ubuntu:latest"
ALPINE_IMAGE_NAME = "alpine:latest"



def test_http_port(run, check_http_get):

    secret = str(uuid())

    # Run http job
    command = f"bash -c \"echo '{secret}' > /usr/share/nginx/html/secret.txt; timeout 5m /usr/sbin/nginx -g 'daemon off;'\""
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
            "--non-preemptible",
            "-d",
            "nginx with secret file",
            NGINX_IMAGE_NAME,
            command,
        ]
    )
    assert not captured.err
    job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)
    wait_job_change_state_from(run, job_id, Status.PENDING, Status.FAILED)

    captured = run(["job", "status", job_id])
    url = re.search(r"Http URL:\s+(\S+)", captured.out).group(1)

    secret_url = url + "/secret.txt"
    # external ingress
    probe = check_http_get(secret_url)
    assert probe.strip() == secret

    command = f"wget -q {secret_url} -O -"
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
            "--non-preemptible",
            "-d",
            "secret fetcher",
            ALPINE_IMAGE_NAME,
            command,
        ]
    )
    assert not captured.err
    job_id = re.match("Job ID: (.+) Status:", captured.out).group(1)
    wait_job_change_state_to(run, job_id, Status.SUCCEEDED, Status.FAILED)

    captured = run(["job", "logs", job_id])
    assert not captured.err
    assert captured.out == secret

    #  internal hostname getting hack
    #  TODO replace next code when
    #  https://github.com/neuromation/platform-api-clients/issues/516 will be implemented
