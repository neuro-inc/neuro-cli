import asyncio
import sys
from json import dumps

import apolo_sdk

from .const import EX_DATAERR, EX_UNAVAILABLE, EX_USAGE


def error(message: str, exit_code: int) -> None:
    print(message)
    exit(exit_code)


async def async_main(action: str) -> None:
    if action == "store":
        error("Please use `apolo login` instead `docker login ...`", EX_UNAVAILABLE)
    elif action == "erase":
        print("Please use `apolo logout` instead `docker logout ...`", EX_UNAVAILABLE)
    else:
        async with apolo_sdk.get() as client:
            config = client.config
            registry = sys.stdin.readline().strip()
            apolo_registry = config.registry_url.host
            if registry != apolo_registry:
                error(
                    f"Unknown registry {registry}. "
                    "apolo configured with {apolo_registry}.",
                    EX_DATAERR,
                )
            token = await config.token()
            payload = {"Username": "token", "Secret": token}
            print(dumps(payload))


def main() -> None:
    if len(sys.argv) == 1 or sys.argv[1] not in ["store", "get", "erase"]:
        error(
            "Apolo Platform docker credential helper.\n:Service tool, not for use",
            EX_USAGE,
        )
    action = sys.argv[1]
    asyncio.run(async_main(action))
