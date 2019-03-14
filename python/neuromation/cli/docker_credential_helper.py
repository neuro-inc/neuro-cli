from .rc import ConfigFactory
from .const import EX_USAGE, EX_UNAVAILABLE, EX_DATAERR
import sys
from yarl import URL
from json import dumps


def main():
    print('Bingo here')
    if len(sys.argv) < 2 or sys.argv[1] not in ['store', 'get', 'erase']:
        print('Neuromation docker credential helper.')
        print('Service tool, not for use')
        exit(EX_USAGE)
    action = sys.argv[1]
    if action == 'store':
        print('Neuromation docker credential helper.')
        print('Please use `neuro login` instead `docker login ...`')
        exit(EX_UNAVAILABLE)
    elif action == 'erase':
        print('Neuromation docker credential helper.')
        print('Please use `neuro logout` instead `docker logout ...`')
        exit(EX_UNAVAILABLE)
    else:
        config = ConfigFactory.load()
        registry = sys.stdin.readline().strip()
        neuro_registry = URL(config.registry_url).host
        if registry != neuro_registry:
            print('Neuromation docker credential helper.')
            print(f'Unknown registry: {registry}. neuro configured with {neuro_registry}.')
            exit(EX_DATAERR)
        payload = {'Username': 'token', 'Secret': config.auth}
        print(dumps(payload))