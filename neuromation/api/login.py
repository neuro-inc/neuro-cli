import abc
import asyncio
import base64
import errno
import hashlib
import secrets
import time
from dataclasses import dataclass, field
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Type,
    cast,
)

import aiohttp
from aiohttp import ClientResponseError, ClientSession
from aiohttp.web import (
    Application,
    AppRunner,
    HTTPBadRequest,
    HTTPForbidden,
    HTTPFound,
    HTTPUnauthorized,
    Request,
    Response,
    TCPSite,
)
from yarl import URL

from .core import DEFAULT_TIMEOUT
from .users import get_token_username
from .utils import asynccontextmanager


def urlsafe_unpadded_b64encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


class AuthException(Exception):
    pass


class AuthCode:
    def __init__(self, callback_url: Optional[URL] = None) -> None:
        self._future: asyncio.Future[str] = asyncio.Future()

        self._verifier = urlsafe_unpadded_b64encode(secrets.token_bytes(32))
        digest = hashlib.sha256(self._verifier.encode()).digest()
        self._challenge = urlsafe_unpadded_b64encode(digest)
        self._challenge_method = "S256"

        self._callback_url = callback_url

    @property
    def verifier(self) -> str:
        return self._verifier

    @property
    def challenge(self) -> str:
        return self._challenge

    @property
    def challenge_method(self) -> str:
        return self._challenge_method

    def set_value(self, value: str) -> None:
        if not self._future.cancelled():
            self._future.set_result(value)

    @property
    def callback_url(self) -> URL:
        assert self._callback_url
        return self._callback_url

    @callback_url.setter
    def callback_url(self, value: URL) -> None:
        self._callback_url = value

    def set_exception(self, exc: Exception) -> None:
        if not self._future.cancelled():
            self._future.set_exception(exc)

    def cancel(self) -> None:
        self._future.cancel()

    async def wait(self, timeout_s: float = 60.0) -> str:
        try:
            await asyncio.wait_for(self._future, timeout_s)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            raise AuthException("failed to get an authorization code")
        return self._future.result()


class AuthCodeCallbackClient(abc.ABC):
    def __init__(self, url: URL, client_id: str, audience: str) -> None:
        self._url = url
        self._client_id = client_id
        self._audience = audience

    async def request(self, code: AuthCode) -> AuthCode:
        url = self._url.with_query(
            response_type="code",
            code_challenge=code.challenge,
            code_challenge_method=code.challenge_method,
            client_id=self._client_id,
            redirect_uri=str(code.callback_url),
            scope="offline_access",
            audience=self._audience,
        )
        await self._request(url, code)
        await code.wait()
        return code

    @abc.abstractmethod
    async def _request(self, url: URL, code: AuthCode) -> None:
        pass


class WebBrowserAuthCodeCallbackClient(AuthCodeCallbackClient):
    def __init__(
        self,
        url: URL,
        client_id: str,
        audience: str,
        show_browser_cb: Callable[[URL], Awaitable[None]],
    ) -> None:
        super().__init__(url=url, client_id=client_id, audience=audience)
        self._show_browser_cb = show_browser_cb

    async def _request(self, url: URL, code: AuthCode) -> None:
        await self._show_browser_cb(url)


class HeadlessAuthCodeCallbackClient(AuthCodeCallbackClient):
    def __init__(
        self,
        url: URL,
        client_id: str,
        audience: str,
        get_auth_code_cb: Callable[[URL], Awaitable[str]],
    ) -> None:
        super().__init__(url=url, client_id=client_id, audience=audience)
        self._get_auth_code_cb = get_auth_code_cb

    async def _request(self, url: URL, code: AuthCode) -> None:
        try:
            auth_code = await self._get_auth_code_cb(url)
            assert auth_code
            code.set_value(auth_code)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            code.set_exception(exc)


class AuthCodeCallbackHandler:
    def __init__(self, code: AuthCode, redirect_url: Optional[URL] = None) -> None:
        self._code = code
        self._redirect_url = redirect_url

    async def handle(self, request: Request) -> Response:
        if "error" in request.query:
            await self._handle_error(request)

        code = request.query.get("code")

        if not code:
            self._code.cancel()
            raise HTTPBadRequest(text="The 'code' query parameter is missing.")

        self._code.set_value(code)

        if self._redirect_url:
            raise HTTPFound(self._redirect_url)
        return Response(text="OK")

    async def _handle_error(self, request: Request) -> None:
        error = request.query["error"]
        description = request.query.get("error_description", "")

        exc_factory: Type[Exception]
        if error == "unauthorized":
            exc_factory = HTTPUnauthorized
        elif error == "access_denied":
            exc_factory = HTTPForbidden
        else:
            exc_factory = HTTPBadRequest

        self._code.set_exception(AuthException(description))
        raise exc_factory(text=description)


def create_auth_code_app(
    code: AuthCode, redirect_url: Optional[URL] = None
) -> Application:
    app = Application()
    handler = AuthCodeCallbackHandler(code, redirect_url=redirect_url)
    app.router.add_get("/", handler.handle)
    return app


@asynccontextmanager
async def create_app_server_once(
    app: Application, *, host: str = "127.0.0.1", port: int = 8080
) -> AsyncIterator[URL]:
    runner = AppRunner(app, access_log=None)
    try:
        await runner.setup()
        site = TCPSite(runner, host, port, shutdown_timeout=0.0)
        await site.start()
        yield URL(site.name)
    finally:
        await runner.shutdown()
        await runner.cleanup()


@asynccontextmanager
async def create_app_server(
    app: Application, *, host: str = "127.0.0.1", ports: Sequence[int] = (8080,)
) -> AsyncIterator[URL]:
    for port in ports:
        try:
            async with create_app_server_once(app, host=host, port=port) as url:
                yield url
            return
        except OSError as err:
            if err.errno != errno.EADDRINUSE:
                raise
    else:
        raise RuntimeError("No free ports.")


@dataclass(frozen=True)
class _AuthToken:
    token: str
    expiration_time: int
    refresh_token: str = field(repr=False)

    time_factory: Callable[[], float] = field(
        default=time.time, repr=False, compare=False
    )

    @property
    def is_expired(self) -> bool:
        tf = self.time_factory  # type: ignore
        current_time = int(tf())  # type: ignore
        return self.expiration_time <= current_time

    @property
    def username(self) -> str:
        return get_token_username(self.token)

    @classmethod
    def create(
        cls,
        token: str,
        expires_in: int,
        refresh_token: str,
        expiration_ratio: float = 0.75,
        time_factory: Optional[Callable[[], float]] = None,
    ) -> "_AuthToken":
        time_factory = time_factory or cls.time_factory
        expiration_time = int(time_factory()) + int(expires_in * expiration_ratio)
        return cls(
            token=token,
            expiration_time=expiration_time,
            refresh_token=refresh_token,
            time_factory=time_factory,
        )

    @classmethod
    def create_non_expiring(cls, token: str) -> "_AuthToken":
        # NOTE: for backward compatibility we assume that manually set token
        # expires in 3 years.
        expires_in = 60 * 60 * 24 * 365 * 3  # 3 years
        return cls.create(token, expires_in=expires_in, refresh_token="")


class AuthTokenClient:
    def __init__(
        self,
        connector: aiohttp.BaseConnector,
        url: URL,
        client_id: str,
        timeout: aiohttp.ClientTimeout,
    ) -> None:
        self._url = url
        self._client_id = client_id

        self._client = ClientSession(
            connector=connector, connector_owner=False, timeout=timeout
        )

    async def close(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> "AuthTokenClient":
        return self

    async def __aexit__(self, *_: Sequence[Any]) -> None:
        await self.close()

    async def request(self, code: AuthCode) -> _AuthToken:
        payload = dict(
            grant_type="authorization_code",
            code_verifier=code.verifier,
            code=await code.wait(),
            client_id=self._client_id,
            redirect_uri=str(code.callback_url),
        )
        async with self._client.post(self._url, json=payload) as resp:
            try:
                resp.raise_for_status()
            except ClientResponseError as exc:
                raise AuthException("failed to get an access token.") from exc
            resp_payload = await resp.json()
            return _AuthToken.create(
                token=resp_payload["access_token"],
                expires_in=resp_payload["expires_in"],
                refresh_token=resp_payload["refresh_token"],
            )

    async def refresh(self, token: _AuthToken) -> _AuthToken:
        payload = dict(
            grant_type="refresh_token",
            refresh_token=token.refresh_token,
            client_id=self._client_id,
        )
        async with self._client.post(self._url, json=payload) as resp:
            try:
                resp.raise_for_status()
            except ClientResponseError as exc:
                raise AuthException("failed to get an access token.") from exc
            resp_payload = await resp.json()
            return _AuthToken.create(
                token=resp_payload["access_token"],
                expires_in=resp_payload["expires_in"],
                refresh_token=token.refresh_token,
            )


@dataclass(frozen=True)
class RunPreset:
    cpu: float
    memory_mb: int
    gpu: Optional[int] = None
    gpu_model: Optional[str] = None


@dataclass(frozen=True)
class _ClusterConfig:
    registry_url: URL
    storage_url: URL
    users_url: URL
    monitoring_url: URL
    resource_presets: Dict[str, RunPreset]

    @classmethod
    def create(
        cls,
        registry_url: URL,
        storage_url: URL,
        users_url: URL,
        monitoring_url: URL,
        resource_presets: Dict[str, RunPreset],
    ) -> "_ClusterConfig":
        return cls(
            registry_url, storage_url, users_url, monitoring_url, resource_presets
        )

    def is_initialized(self) -> bool:
        return bool(
            self.registry_url
            and self.storage_url
            and self.users_url
            and self.monitoring_url
            and self.resource_presets
        )


@dataclass(frozen=True)
class _AuthConfig:
    auth_url: URL
    token_url: URL

    client_id: str
    audience: str

    headless_callback_url: URL

    callback_urls: Sequence[URL] = (
        URL("http://127.0.0.1:54540"),
        URL("http://127.0.0.1:54541"),
        URL("http://127.0.0.1:54542"),
    )

    success_redirect_url: Optional[URL] = None

    @property
    def callback_host(self) -> str:
        return cast(str, self.callback_urls[0].host)

    @property
    def callback_ports(self) -> List[int]:
        return [cast(int, url.port) for url in self.callback_urls]

    def is_initialized(self) -> bool:
        return bool(
            self.auth_url
            and self.token_url
            and self.client_id
            and self.audience
            and self.headless_callback_url
        )

    @classmethod
    def create(
        cls,
        auth_url: URL,
        token_url: URL,
        client_id: str,
        audience: str,
        headless_callback_url: URL,
        success_redirect_url: Optional[URL] = None,
        callback_urls: Optional[Sequence[URL]] = None,
    ) -> "_AuthConfig":
        return cls(
            auth_url=auth_url,
            token_url=token_url,
            client_id=client_id,
            audience=audience,
            headless_callback_url=headless_callback_url,
            success_redirect_url=success_redirect_url,
            callback_urls=callback_urls or cls.callback_urls,
        )


async def refresh_token(
    connector: aiohttp.BaseConnector,
    config: _AuthConfig,
    token: _AuthToken,
    timeout: aiohttp.ClientTimeout,
) -> _AuthToken:
    async with AuthTokenClient(
        connector, url=config.token_url, client_id=config.client_id, timeout=timeout
    ) as token_client:
        if token.is_expired:
            return await token_client.refresh(token)
        return token


class BaseNegotiator(abc.ABC):
    def __init__(
        self,
        connector: aiohttp.BaseConnector,
        config: _AuthConfig,
        timeout: aiohttp.ClientTimeout,
    ) -> None:
        self._config = config
        self._timeout = timeout
        self._connector = connector

    @abc.abstractmethod
    async def get_code(self) -> AuthCode:
        pass

    async def refresh_token(self, token: Optional[_AuthToken] = None) -> _AuthToken:
        async with AuthTokenClient(
            self._connector,
            url=self._config.token_url,
            client_id=self._config.client_id,
            timeout=self._timeout,
        ) as token_client:
            if not token:
                code = await self.get_code()
                return await token_client.request(code)

            if token.is_expired:
                return await token_client.refresh(token)

            return token


class AuthNegotiator(BaseNegotiator):
    def __init__(
        self,
        connector: aiohttp.BaseConnector,
        config: _AuthConfig,
        show_browser_cb: Callable[[URL], Awaitable[None]],
        timeout: aiohttp.ClientTimeout,
    ) -> None:
        super().__init__(connector, config, timeout)
        self._show_browser_cb = show_browser_cb

    async def get_code(self) -> AuthCode:
        code = AuthCode()
        app = create_auth_code_app(code, redirect_url=self._config.success_redirect_url)

        async with create_app_server(
            app, host=self._config.callback_host, ports=self._config.callback_ports
        ) as url:
            code.callback_url = url
            code_callback_client = WebBrowserAuthCodeCallbackClient(
                url=self._config.auth_url,
                client_id=self._config.client_id,
                audience=self._config.audience,
                show_browser_cb=self._show_browser_cb,
            )
            return await code_callback_client.request(code)


class HeadlessNegotiator(BaseNegotiator):
    def __init__(
        self,
        connector: aiohttp.BaseConnector,
        config: _AuthConfig,
        get_auth_code_cb: Callable[[URL], Awaitable[str]],
        timeout: aiohttp.ClientTimeout,
    ) -> None:
        super().__init__(connector, config, timeout)
        self._get_auth_code_cb = get_auth_code_cb

    async def get_code(self) -> AuthCode:
        code = AuthCode()
        code.callback_url = self._config.headless_callback_url

        code_callback_client = HeadlessAuthCodeCallbackClient(
            url=self._config.auth_url,
            client_id=self._config.client_id,
            audience=self._config.audience,
            get_auth_code_cb=self._get_auth_code_cb,
        )
        return await code_callback_client.request(code)


@dataclass(frozen=True)
class _ServerConfig:
    auth_config: _AuthConfig
    cluster_config: _ClusterConfig


class ConfigLoadException(Exception):
    pass


async def get_server_config(
    connector: aiohttp.BaseConnector, url: URL, token: Optional[str] = None
) -> _ServerConfig:
    async with aiohttp.ClientSession(
        timeout=DEFAULT_TIMEOUT, connector=connector, connector_owner=False
    ) as client:
        headers: Dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        async with client.get(url / "config", headers=headers) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Unable to get server configuration: {resp.status}")
            payload = await resp.json()
            # TODO (ajuszkowski, 5-Feb-2019) validate received data
            success_redirect_url = URL(payload.get("success_redirect_url", "")) or None
            callback_urls = payload.get("callback_urls")
            callback_urls = (
                tuple(URL(u) for u in callback_urls)
                if callback_urls is not None
                else _AuthConfig.callback_urls
            )
            headless_callback_url = URL(payload["headless_callback_url"])
            auth_config = _AuthConfig(
                auth_url=URL(payload["auth_url"]),
                token_url=URL(payload["token_url"]),
                client_id=payload["client_id"],
                audience=payload["audience"],
                success_redirect_url=success_redirect_url,
                callback_urls=callback_urls,
                headless_callback_url=headless_callback_url,
            )
            cluster_config = _ClusterConfig(
                registry_url=URL(payload.get("registry_url", "")),
                storage_url=URL(payload.get("storage_url", "")),
                users_url=URL(payload.get("users_url", "")),
                monitoring_url=URL(payload.get("monitoring_url", "")),
                resource_presets={
                    data["name"]: RunPreset(
                        cpu=data["cpu"],
                        memory_mb=data["memory_mb"],
                        gpu=data.get("gpu"),
                        gpu_model=data.get("gpu_model"),
                    )
                    for data in payload.get("resource_presets", ())
                },
            )
            if headers and not cluster_config.is_initialized():
                raise AuthException("Cannot authorize user")
            return _ServerConfig(cluster_config=cluster_config, auth_config=auth_config)
