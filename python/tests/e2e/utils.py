import os
from time import sleep

import pytest


BLOCK_SIZE_MB = 16
FILE_COUNT = 1
FILE_SIZE_MB = 16
GENERATION_TIMEOUT_SEC = 120
RC_TEXT = "url: http://platform.dev.neuromation.io/api/v1\nauth: {token}"
UBUNTU_IMAGE_NAME = "ubuntu:latest"
format_list = "{type:<15}{size:<15,}{name:<}".format
FS_SYNC_TIME = os.environ.get("CLIENT_TEST_E2E_FS_SYNC_TIME", 15)


def fs_sync(multiplier: float = 1.0):
    sleep(multiplier * FS_SYNC_TIME)
