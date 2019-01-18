from time import sleep

from _sha1 import sha1


BLOCK_SIZE_MB = 16
FILE_COUNT = 1
FILE_SIZE_MB = 16
FILE_SIZE_B = FILE_SIZE_MB * 1024 * 1024
GENERATION_TIMEOUT_SEC = 120
RC_TEXT = "url: https://platform.dev.neuromation.io/api/v1\nauth: {token}"
UBUNTU_IMAGE_NAME = "ubuntu:latest"
format_list = "{type:<15}{size:<15,}{name:<}".format
format_list_pattern = "(file|directory)\\s*\\d+\\s*{name}".format


def hash_hex(file):
    _hash = sha1()
    with open(file, "rb") as f:
        for block in iter(lambda: f.read(BLOCK_SIZE_MB * 1024 * 1024), b""):
            _hash.update(block)

    return _hash.hexdigest()


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
