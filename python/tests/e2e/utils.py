from time import sleep


BLOCK_SIZE_MB = 16
FILE_SIZE_MB = 16
FILE_SIZE_B = FILE_SIZE_MB * 1024 * 1024
GENERATION_TIMEOUT_SEC = 120
RC_TEXT = (
    "url: https://dev.neu.ro/api/v1\n"
    "registry_url: https://registry-dev.neu.ro\n"
    "auth: {token}"
)
UBUNTU_IMAGE_NAME = "ubuntu:latest"
format_list = "{type:<15}{size:<15,}{name:<}".format
format_list_pattern = "(file|directory)\\s*\\d+\\s*{name}".format

file_format_re = (
    r"(?P<type>[-d])"
    r"(?P<permission>[rwm])\s+"
    r"(?P<size>\d+)\s+"
    r"(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
    r"(?P<name>.+)"
)

JOB_TINY_CONTAINER_PARAMS = ["-m", "20M", "-c", "0.1", "-g", "0", "--non-preemptible"]


def attempt(attempts: int = 4, sleep_time: float = 15.0):
    """
    This decorator allow function fail up to _attempts_ times with
    pause _sleep_timeout_ seconds between each attempt
    :param attempts:
    :param sleep_time:
    :return:
    """

    def _attempt(func, *args, **kwargs):
        def wrapped(*args, **kwargs):
            nonlocal attempts
            while True:
                attempts -= 1
                if attempts > 0:
                    try:
                        return func(*args, **kwargs)
                    except BaseException:
                        pass
                    sleep(sleep_time)
                else:
                    return func(*args, **kwargs)

        return wrapped

    return _attempt
