from dataclasses import dataclass
from functools import wraps
from typing import Optional

import aiohttp
import click
from yarl import URL

from neuromation.clientv2 import ClientV2
from neuromation.utils import run

from . import rc


@dataclass(frozen=True)
class Context:
    token: str
    url: URL

    def make_client(self, *, timeout: Optional[aiohttp.ClientTimeout] = None):
        kwargs = {}
        if timeout is not None:
            kwargs['timeout'] = timeout
        return ClientV2(self.url, self.token, **kwargs)


def run_async(callback):
    @wraps(callback)
    def wrapper(*args, **kwargs):
        return run(callback(*args, **kwargs))

    return wrapper


def load_token():
    config = rc.ConfigFactory.load()
    return config.auth


def load_url():
    config = rc.ConfigFactory.load()
    return config.auth


class DeprecatedGroup(click.MultiCommand):
    def __init__(self, origin, name=None, **attrs):
        attrs.setdefault("help", f"Alias for {origin.name}")
        attrs.setdefault("deprecated", True)
        super().__init__(name, **attrs)
        self.origin = origin

    def get_command(self, ctx, cmd_name):
        return self.origin.get_command(ctx, cmd_name)

    def list_commands(self, ctx):
        return self.origin.list_commands(ctx)
