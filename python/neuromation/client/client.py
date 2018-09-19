import asyncio
import logging
from builtins import FileNotFoundError as BuiltinFileNotFoundError

from neuromation.http import fetch, session

from .requests import Request, build

log = logging.getLogger(__name__)


class ClientError(Exception):
    pass


class IllegalArgumentError(ValueError):
    pass


class AuthError(ClientError):
    pass


class AuthenticationError(AuthError):
    pass


class AuthorizationError(AuthError):
    pass


class IOError(ClientError):
    pass


class FileNotFoundError(IOError, BuiltinFileNotFoundError):
    pass


class AccessDeniedError(IOError):
    pass


class NetworkError(IOError):
    pass


class ModelsError(ValueError):
    pass


class ApiClient:
    def __init__(self, url: str, token: str, *, loop=None):
        self._url = url
        self._loop = loop if loop else asyncio.get_event_loop()
        self._session = self.loop.run_until_complete(session(token=token))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.loop.run_until_complete(self.close())

    @property
    def loop(self):
        return self._loop

    async def close(self):
        if self._session and self._session.closed:
            return

        await self._session.close()
        self._session = None

    async def _fetch(self, request: Request):
        return await fetch(
            build(request),
            session=self._session,
            url=self._url)

    def _fetch_sync(self, request: Request):
        res = self._loop.run_until_complete(self._fetch(request))
        log.debug(res)

        return res
