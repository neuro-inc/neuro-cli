import os
from time import sleep


BLOCK_SIZE_MB = 16
FILE_COUNT = 1
FILE_SIZE_MB = 16
GENERATION_TIMEOUT_SEC = 120
RC_TEXT = "url: http://platform.dev.neuromation.io/api/v1\nauth: {token}"
UBUNTU_IMAGE_NAME = "ubuntu:latest"
format_list = "{type:<15}{size:<15,}{name:<}".format
FS_SYNC_TIME = int(os.environ.get("CLIENT_TEST_E2E_FS_SYNC_TIME", 20))


def fs_sync(periods: float = 1.0):
    """
    Just wait given count of time periods for FS sync
    :param periods:
    :return:
    """
    sleep(periods * FS_SYNC_TIME)


def try_or_assert(func: callable, attempts: int = 4, periods: float = 1.0):
    """
    Try to execute func few times
    :param func: function to execute
    :param attempts: attempts count
    :param periods: how many periods waits before next try
    :return:
    """
    num = attempts
    while True:
        num -= 1
        if num > 0:
            try:
                result = func()
                return result
            except BaseException:
                pass
        else:
            return func()
        fs_sync(periods)
