BLOCK_SIZE_MB = 16
FILE_SIZE_MB = 16
FILE_SIZE_B = FILE_SIZE_MB * 1024 * 1024
GENERATION_TIMEOUT_SEC = 120
RC_TEXT = """
auth_config:
  audience: https://platform.dev.neuromation.io
  auth_url: https://dev-neuromation.auth0.com/authorize
  callback_urls:
  - http://127.0.0.1:54540
  - http://127.0.0.1:54541
  - http://127.0.0.1:54542
  client_id: CLIENT-ID
  success_redirect_url: https://neu.ro/#running-your-first-job
  token_url: https://dev-neuromation.auth0.com/oauth/token
auth_token:
  expiration_time: 1713014496
  refresh_token: refresh-token
  token: {token}
pypi:
  check_timestamp: 0
  pypi_version: 0.0.0
cluster_config:
  monitoring_url: https://dev.neu.ro/api/v1/jobs
  registry_url: https://registry-dev.neu.ro
  storage_url: https://dev.neu.ro/api/v1/storage
  users_url: https://dev.neu.ro/api/v1/users
url: https://dev.neu.ro/api/v1
"""

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

JOB_TINY_CONTAINER_PARAMS = ["-m", "20M", "-c", "0.1", "-g", "0", "--non-preemptible"]


class JobWaitStateStopReached(AssertionError):
    pass
