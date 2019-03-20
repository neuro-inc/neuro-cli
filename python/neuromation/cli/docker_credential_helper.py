import sys
from json import dumps

from yarl import URL

from .const import EX_DATAERR, EX_NOUSER, EX_UNAVAILABLE, EX_USAGE
from .rc import ConfigFactory


def error(message: str, exit_code: int) -> None:
    print(message)
    exit(exit_code)


def main() -> None:
    if len(sys.argv) == 1 or sys.argv[1] not in ["store", "get", "erase"]:
        error(
            "Neuromation docker credential helper.\nService tool, not for use", EX_USAGE
        )
    action = sys.argv[1]
    config = ConfigFactory.load()
    if action == "store":
        error("Please use `neuro login` instead `docker login ...`", EX_UNAVAILABLE)
    elif action == "erase":
        print("Please use `neuro logout` instead `docker logout ...`", EX_UNAVAILABLE)
    else:
        registry = sys.stdin.readline().strip()
        neuro_registry = URL(config.registry_url).host
        if registry != neuro_registry:
            error(
                f"Unknown registry {registry}. "
                "neuro configured with {neuro_registry}.",
                EX_DATAERR,
            )
        if not config.auth:
            error("Not logged in. Please use ``neuro login` first.", EX_NOUSER)

        payload = {"Username": "token", "Secret": config.auth}
        print(dumps(payload))
