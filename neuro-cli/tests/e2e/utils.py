BLOCK_SIZE_MB = 16
FILE_SIZE_MB = 16
FILE_SIZE_B = FILE_SIZE_MB * 1024 * 1024
GENERATION_TIMEOUT_SEC = 120

UBUNTU_IMAGE_NAME = "ubuntu:latest"
NGINX_IMAGE_NAME = "nginx:latest"
ALPINE_IMAGE_NAME = "alpine:latest"

format_list = "{type:<15}{size:<15,}{name:<}".format
format_list_pattern = "(file|directory)\\s*\\d+\\s*{name}".format

file_format_re = (
    r"(?P<type>[-d])"
    r"(?P<permission>[rwm])\s+"
    r"(?P<size>\d+)\s+"
    r"(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
    r"(?P<name>.+)"
)

JOB_TINY_CONTAINER_PRESET = "cpu-micro"


class JobWaitStateStopReached(AssertionError):
    pass
