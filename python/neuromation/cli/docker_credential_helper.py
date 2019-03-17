import sys
from json import dumps

from yarl import URL

from .const import EX_DATAERR, EX_UNAVAILABLE, EX_USAGE
from .rc import ConfigFactory


def main() -> None:
    if len(sys.argv) == 1 or sys.argv[1] not in ["store", "get", "erase"]:
        print("Neuromation docker credential helper.")
        print("Service tool, not for use")
        exit(EX_USAGE)
    action = sys.argv[1]
    config = ConfigFactory.load()
    if action == "store":
        if config.auth:
            print("Please use `neuro login` instead `docker login ...`")
            exit(EX_UNAVAILABLE)
    elif action == "erase":
        if config.auth:
            print("Please use `neuro logout` instead `docker logout ...`")
            exit(EX_UNAVAILABLE)
    else:
        registry = sys.stdin.readline().strip()
        neuro_registry = URL(config.registry_url).host
        if registry != neuro_registry:
            print("Neuromation docker credential helper.")
            print(
                f"Unknown registry: {registry}. neuro configured with {neuro_registry}."
            )
            exit(EX_DATAERR)
        payload = {"Username": "token", "Secret": config.auth}
        print(dumps(payload))
