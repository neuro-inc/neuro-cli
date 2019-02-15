import enum
from time import sleep, time


JOB_TIMEOUT = 60 * 5
JOB_WAIT_SLEEP_SECONDS = 2


class Status(str, enum.Enum):
    PENDING = "Status: pending"
    NOT_ENOUGH = "Cluster doesn't have resources to fulfill request"
    RUNNING = "Status: running"
    FAILED = "Status: failed"
    SUCCEEDED = "Status: succeeded"


def assert_job_state(run_cli, job_id, state):
    captured = run_cli(["job", "status", job_id])
    assert state in captured.out


def wait_job_change_state_from(run_cli, job_id, str_wait, str_stop=None):
    out = str_wait
    start_time = time()
    while (str_wait in out) and (int(time() - start_time) < JOB_TIMEOUT):
        sleep(JOB_WAIT_SLEEP_SECONDS)
        captured = run_cli(["job", "status", job_id])
        out = captured.out
        if str_stop and str_stop in out:
            raise AssertionError(f"failed running job {job_id}: {str_stop}")


def wait_job_change_state_to(run_cli, job_id, str_target, str_stop=None):
    assert str_target
    out = ""
    start_time = time()
    while str_target not in out:
        sleep(JOB_WAIT_SLEEP_SECONDS)
        captured = run_cli(["job", "status", job_id])
        out = captured.out
        if str_stop and str_stop in out:
            raise AssertionError(
                f"failed running job {job_id}: '{str_stop}' in '{out}'"
            )
        if int(time() - start_time) > JOB_TIMEOUT:
            raise AssertionError(f"timeout exceeded, last output: '{out}'")
