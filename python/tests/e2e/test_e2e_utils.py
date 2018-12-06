from time import sleep, time


JOB_TIMEOUT = 5 * 60
JOB_WAIT_SLEEP_SECONDS = 5


def wait_for_job_to_change_state_to(run, job_id, str_target, str_error=None):
    assert str_target
    out = ""
    start_time = time()
    while str_target not in out:
        _, captured = run(["job", "status", job_id])
        out = captured.out
        if str_error and str_error in out:
            raise Exception(f"failed running job {job_id}: '{str_error}'")
        if int(time() - start_time) > JOB_TIMEOUT:
            raise Exception("timeout exceeded")
        sleep(JOB_WAIT_SLEEP_SECONDS)
