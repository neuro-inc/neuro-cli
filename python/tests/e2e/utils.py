import re
import time
from time import sleep
from typing import Sequence

from neuromation.client import FileStatus, FileStatusType


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


def output_to_files(output: str) -> Sequence[FileStatus]:
    result = []
    for match in re.finditer(file_format_re, output):
        type = FileStatusType.FILE
        if match["type"] == "d":
            type = FileStatusType.DIRECTORY

        permission = "read"
        if match["permission"] == "w":
            permission = "write"
        elif match["permission"] == "m":
            permission = "manage"

        ts = int(time.mktime(time.strptime(match["time"], "%Y-%m-%d %H:%M:%S")))

        result.append(
            FileStatus(
                path=match["name"],
                size=int(match["size"]),
                type=type,
                modification_time=ts,
                permission=permission,
            )
        )
    return result


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
