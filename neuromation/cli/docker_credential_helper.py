import sys
from json import dumps

from neuromation.api import get
from neuromation.utils import run

from .const import EX_DATAERR, EX_UNAVAILABLE, EX_USAGE


def error(message: str, exit_code: int) -> None:
    print(message)
    exit(exit_code)


async def async_main(action: str) -> None:
    if action == "store":
        error("Please use `neuro login` instead `docker login ...`", EX_UNAVAILABLE)
    elif action == "erase":
        print("Please use `neuro logout` instead `docker logout ...`", EX_UNAVAILABLE)
    else:
        async with get() as client:
            config = client._config
            config.check_initialized()
            registry = sys.stdin.readline().strip()
            neuro_registry = config.cluster_config.registry_url.host
            if registry != neuro_registry:
                error(
                    f"Unknown registry {registry}. "
                    "neuro configured with {neuro_registry}.",
                    EX_DATAERR,
                )
            payload = {"Username": "token", "Secret": config.auth_token.token}
            print(dumps(payload))


def main() -> None:
    if len(sys.argv) == 1 or sys.argv[1] not in ["store", "get", "erase"]:
        error(
            "Neuromation docker credential helper.\nService tool, not for use", EX_USAGE
        )
    action = sys.argv[1]
    run(async_main(action))
