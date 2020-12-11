import sys
from json import dumps

import neuro_sdk

from .asyncio_utils import run
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
        async with neuro_sdk.get() as client:
            config = client.config
            registry = sys.stdin.readline().strip()
            neuro_registry = config.registry_url.host
            if registry != neuro_registry:
                error(
                    f"Unknown registry {registry}. "
                    "neuro configured with {neuro_registry}.",
                    EX_DATAERR,
                )
            token = await config.token()
            payload = {"Username": "token", "Secret": token}
            print(dumps(payload))


def main() -> None:
    if len(sys.argv) == 1 or sys.argv[1] not in ["store", "get", "erase"]:
        error(
            "Neuro Platform docker credential helper.\n:Service tool, not for use",
            EX_USAGE,
        )
    action = sys.argv[1]
    run(async_main(action))
