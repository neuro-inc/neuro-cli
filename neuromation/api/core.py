import asyncio
import contextlib
import errno
import json as jsonmodule
import logging
import sqlite3
import time
from http.cookies import Morsel, SimpleCookie
from types import SimpleNamespace
from typing import Any, AsyncIterator, Dict, Mapping, Optional

import aiohttp
from aiohttp import WSMessage
from multidict import CIMultiDict
from yarl import URL

from .tracing import gen_trace_id
from .utils import asynccontextmanager


log = logging.getLogger(__name__)

SESSION_COOKIE_MAXAGE = 5 * 60  # 5 min

SCHEMA = {
    "cookie_session": "CREATE TABLE cookie_session (cookie TEXT, timestamp REAL)",
}
DROP = {"cookie_session": "DROP TABLE IF EXISTS cookie_session"}


DEFAULT_TIMEOUT = aiohttp.ClientTimeout(None, None, 60, 60)


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


class ResourceNotFound(ValueError):
    pass


class ServerNotAvailable(ValueError):
    pass


class _Core:
    """Transport provider for public API client.

    Internal class.
    """

    def __init__(
        self, session: aiohttp.ClientSession, trace_id: Optional[str],
    ) -> None:
        self._session = session
        self._trace_id = trace_id
        self._exception_map = {
            400: IllegalArgumentError,
            401: AuthenticationError,
            403: AuthorizationError,
            404: ResourceNotFound,
            405: ClientError,
            502: ServerNotAvailable,
        }
        self._prev_cookie: Optional[Morsel[str]] = None

    def _post_init(self, db: sqlite3.Connection, storage_url: URL) -> None:
        cookie_val = load_cookie(db)
        if cookie_val is not None:
            tmp = SimpleCookie()  # type: ignore
            tmp["NEURO_SESSION"] = cookie_val
            cookie = tmp["NEURO_SESSION"]
            cookie["domain"] = storage_url.host
            cookie["path"] = "/"
            self._session.cookie_jar.update_cookies(
                {"NEURO_SESSION": cookie}  # type: ignore
                # TODO: pass cookie["domain"]
            )

    def _save_cookie(self, db: sqlite3.Connection) -> None:
        for cookie in self._session.cookie_jar:
            if cookie.key == "NEURO_SESSION":
                break
        else:
            return
        save_cookie(db, cookie.value)

    @property
    def timeout(self) -> aiohttp.ClientTimeout:
        # TODO: implement ClientSession.timeout public property for session
        return self._session._timeout

    @property
    def session(self) -> aiohttp.ClientSession:
        return self._session

    async def close(self) -> None:
        pass

    @asynccontextmanager
    async def request(
        self,
        method: str,
        url: URL,
        *,
        auth: str,
        params: Optional[Mapping[str, str]] = None,
        data: Any = None,
        json: Any = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[aiohttp.ClientTimeout] = None,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        assert url.is_absolute()
        log.debug("Fetch [%s] %s", method, url)
        if headers is not None:
            real_headers: CIMultiDict[str] = CIMultiDict(headers)
        else:
            real_headers = CIMultiDict()
        real_headers["Authorization"] = auth
        trace_request_ctx = SimpleNamespace()
        trace_id = self._trace_id
        if trace_id is None:
            trace_id = gen_trace_id()
        trace_request_ctx.trace_id = trace_id
        if params:
            url = url.with_query(params)
        async with self._session.request(
            method,
            url,
            headers=real_headers,
            json=json,
            data=data,
            timeout=timeout,
            trace_request_ctx=trace_request_ctx,
        ) as resp:
            if 400 <= resp.status:
                err_text = await resp.text()
                if resp.content_type.lower() == "application/json":
                    try:
                        payload = jsonmodule.loads(err_text)
                    except ValueError:
                        # One example would be a HEAD request for application/json
                        payload = {}
                    if "error" in payload:
                        err_text = payload["error"]
                else:
                    payload = {}
                if resp.status == 400 and "errno" in payload:
                    os_errno: Any = payload["errno"]
                    os_errno = errno.__dict__.get(os_errno, os_errno)
                    raise OSError(os_errno, err_text)
                err_cls = self._exception_map.get(resp.status, IllegalArgumentError)
                raise err_cls(err_text)
            else:
                try:
                    yield resp
                except GeneratorExit:
                    # There is a bug in CPython and/or aiohttp,
                    # if GeneratorExit is reraised @asynccontextmanager
                    # reports this as an error
                    # Need to investigate and fix.
                    raise asyncio.CancelledError

    async def ws_connect(
        self, abs_url: URL, auth: str, *, headers: Optional[Dict[str, str]] = None
    ) -> AsyncIterator[WSMessage]:
        # TODO: timeout
        assert abs_url.is_absolute(), abs_url
        log.debug("Fetch web socket: %s", abs_url)

        if headers is not None:
            real_headers: CIMultiDict[str] = CIMultiDict(headers)
        else:
            real_headers = CIMultiDict()
        real_headers["Authorization"] = auth

        async with self._session.ws_connect(abs_url, headers=real_headers) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    yield msg


def ensure_schema(db: sqlite3.Connection, *, update: bool) -> bool:
    cur = db.cursor()
    ok = True
    found = set()
    cur.execute("SELECT type, name, sql from sqlite_master")
    for type, name, sql in cur:
        if type not in ("table", "index"):
            continue
        if name in SCHEMA:
            if SCHEMA[name] != sql:
                ok = False
                break
            else:
                found.add(name)

    if not ok or found < SCHEMA.keys():
        for sql in reversed(list(DROP.values())):
            cur.execute(sql)
        for sql in SCHEMA.values():
            cur.execute(sql)
        return True
    return False


def save_cookie(
    db: sqlite3.Connection, cookie: Optional[str], *, now: Optional[float] = None
) -> None:
    if now is None:
        now = time.time()
    ensure_schema(db, update=True)
    cur = db.cursor()
    cur.execute(
        "INSERT INTO cookie_session (cookie, timestamp) VALUES (?, ?)", (cookie, now),
    )
    cur.execute(
        "DELETE FROM cookie_session WHERE timestamp < ?", (now - SESSION_COOKIE_MAXAGE,)
    )
    with contextlib.suppress(sqlite3.OperationalError):
        db.commit()


def load_cookie(
    db: sqlite3.Connection, *, now: Optional[float] = None
) -> Optional[str]:
    if now is None:
        now = time.time()
    if not ensure_schema(db, update=False):
        return None
    cur = db.execute(
        """
                     SELECT cookie FROM cookie_session
                     WHERE timestamp > ?
                     ORDER BY timestamp DESC
                     LIMIT 1""",
        (now - SESSION_COOKIE_MAXAGE,),
    )
    cookie = cur.fetchone()
    return cookie
