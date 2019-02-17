import enum
from time import sleep, time


class Status(str, enum.Enum):
    PENDING = "Status: pending"
    NOT_ENOUGH = "Cluster doesn't have resources to fulfill request"
    RUNNING = "Status: running"
    FAILED = "Status: failed"
    SUCCEEDED = "Status: succeeded"


def assert_job_state(run_cli, job_id, state):
    captured = run_cli(["job", "status", job_id])
    assert state in captured.out
