from time import sleep, time

JOB_TIMEOUT = 10
JOB_WAIT_SLEEP_SECONDS = 2


# TODO (R Zubairov, 09/13/2018): once we would have wait for job


def wait_for_job_to_change_state_from(run, job_id, str_wait):
    out = str_wait
    start_time = time()
    while (str_wait in out) and (int(time() - start_time) < JOB_TIMEOUT):
        sleep(JOB_WAIT_SLEEP_SECONDS)
        _, captured = run(["job", "status", job_id])
        out = captured.out


def wait_for_job_to_change_state_to(run, job_id, str_wait):
    out = ""
    start_time = time()
    while (str_wait not in out) and (int(time() - start_time) < JOB_TIMEOUT):
        sleep(JOB_WAIT_SLEEP_SECONDS)
        _, captured = run(["job", "status", job_id])
        out = captured.out
