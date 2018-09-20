import asyncio
import logging
from builtins import FileNotFoundError as BuiltinFileNotFoundError
from builtins import IOError as BuiltinIOError

from neuromation.http import fetch, session
from neuromation.http.fetch import AccessDeniedError as FetchAccessDeniedError
from neuromation.http.fetch import (BadRequestError, FetchError,
                                    UnauthorizedError)

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


class ClientIOError(ClientError, BuiltinIOError):
    pass


class FileNotFoundError(ClientIOError, BuiltinFileNotFoundError):
    pass


class AccessDeniedError(ClientIOError):
    pass


class NetworkError(ClientIOError):
    pass


class ModelsError(ValueError):
    pass


class ApiClient:

    def __init__(self, url: str, token: str, *, loop=None):
        self._url = url
        self._loop = loop if loop else asyncio.get_event_loop()
        self._session = self.loop.run_until_complete(session(token=token))
        self._exception_map = {
            FetchAccessDeniedError: AuthenticationError,
            UnauthorizedError: AuthenticationError,
            BadRequestError: IllegalArgumentError,
            FetchError: NetworkError
        }

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

        try:
            return await fetch(
                build(request),
                session=self._session,
                url=self._url)
        except (ClientError, FetchError) as error:
            error_class = type(error)
            mapped_class = self._exception_map.get(error_class, error_class)
            raise mapped_class(error)

    def _fetch_sync(self, request: Request):
        res = self._loop.run_until_complete(self._fetch(request))
        log.debug(res)

        return res
