import sys

from yarl import URL

from neuromation.cli import defaults


if sys.version_info >= (3, 7):  # pragma: no cover
    from contextlib import asynccontextmanager  # noqa
else:
    from async_generator import asynccontextmanager  # noqa


def create_registry_url(platform_url: str) -> str:
    if platform_url == "https://dev.ai.neuromation.io/api/v1":
        return "https://registry-dev.ai.neuromation.io"
    if platform_url == "https://staging.ai.neuromation.io/api/v1":
        return "https://registry-staging.ai.neuromation.io"
    platform_url = URL(platform_url)
    host = platform_url.host.replace("platform.", "registry.")
    registry_url = platform_url.with_host(host).with_path("")
    return str(registry_url)
