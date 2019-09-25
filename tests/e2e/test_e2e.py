import re
import subprocess
from typing import List

import pytest

import neuromation
from tests.e2e import Helper
from tests.e2e.utils import UBUNTU_IMAGE_NAME


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

    job_id = helper.run_job_and_wait_state(image=UBUNTU_IMAGE_NAME, command=command)

    try:
        # TODO: implement progressive timeout
        # even 15 secs usually enough for low-load testing
        # but under high load the value should be increased
        capture = helper.run_cli(["job", "top", job_id, "--timeout", "60"])
    except subprocess.CalledProcessError as ex:
        stdout = ex.output
        stderr = ex.stderr
    else:
        stdout = capture.out
        stderr = capture.err

    helper.kill_job(job_id)

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
