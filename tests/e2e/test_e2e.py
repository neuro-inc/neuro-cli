import re
import subprocess
import time
from typing import List
from uuid import uuid4

import pytest

import neuromation
from neuromation.api import JobStatus
from tests.e2e import Helper
from tests.e2e.utils import JOB_TINY_CONTAINER_PARAMS, UBUNTU_IMAGE_NAME


@pytest.mark.e2e
def test_print_version(helper: Helper) -> None:
    expected_out = f"Neuromation Platform Client {neuromation.__version__}"

    captured = helper.run_cli(["--version"])
    assert not captured.err
    assert captured.out == expected_out


@pytest.mark.e2e
def test_print_options(helper: Helper) -> None:
    captured = helper.run_cli(["--options"])
    assert not captured.err
    assert "Options" in captured.out


@pytest.mark.e2e
def test_print_config(helper: Helper) -> None:
    captured = helper.run_cli(["config", "show"])
    assert not captured.err
    assert "API URL: https://dev.neu.ro/api/v1" in captured.out


@pytest.mark.e2e
def test_print_config_token(helper: Helper) -> None:
    captured = helper.run_cli(["config", "show-token"])
    assert not captured.err
    assert captured.out  # some secure information was printed


@pytest.mark.e2e
def test_e2e_job_top(helper: Helper) -> None:
    def split_non_empty_parts(line: str, sep: str) -> List[str]:
        return [part.strip() for part in line.split(sep) if part.strip()]

    command = f"sleep 300"
    job_name = f"test-job-{str(uuid4())[:8]}"
    aux_params = ["--name", job_name]

    helper.run_job_and_wait_state(
        image=UBUNTU_IMAGE_NAME,
        command=command,
        params=JOB_TINY_CONTAINER_PARAMS + aux_params,
    )

    time.sleep(10)  # it makes top command a little stablier

    try:
        helper.run_cli(["job", "top", job_name, "--timeout", "10"])
    except subprocess.CalledProcessError as ex:
        stdout = ex.output
        stderr = ex.stderr
    else:
        assert False, "timeout don't caught"

    helper.kill_job(job_name)

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
            ("year", "2019"),
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
@pytest.mark.parametrize(
    "switch,expected",
    [["--extshm", True], ["--no-extshm", False], [None, True]],  # default is enabled
)
def test_e2e_shm_switch(switch: str, expected: bool, helper: Helper) -> None:
    # Start the df test job
    bash_script = "/bin/df --block-size M --output=target,avail /dev/shm | grep 64M"
    command = f"bash -c '{bash_script}'"
    params = list(JOB_TINY_CONTAINER_PARAMS)
    if switch is not None:
        params.append(switch)

    if expected:
        job_id = helper.run_job_and_wait_state(
            UBUNTU_IMAGE_NAME, command, params, JobStatus.FAILED, JobStatus.SUCCEEDED
        )
        status = helper.job_info(job_id)
        assert status.history.exit_code == 1
    else:
        helper.run_job_and_wait_state(
            UBUNTU_IMAGE_NAME, command, params, JobStatus.SUCCEEDED, JobStatus.FAILED
        )
