import abc
import asyncio
import base64
import errno
import hashlib
import secrets
import time
import webbrowser
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, List, Optional, Sequence

from aiohttp import ClientResponseError, ClientSession
from aiohttp.web import (
    Application,
    AppRunner,
    HTTPBadRequest,
    Request,
    Response,
    TCPSite,
)
from async_generator import asynccontextmanager
from yarl import URL


def urlsafe_unpadded_b64encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


class AuthException(Exception):
    pass


class AuthCode:
    def __init__(self, callback_url: Optional[URL] = None) -> None:
        self._future: asyncio.Future[str] = asyncio.Future()

        self._verifier = self.generate_verifier()
        self._challenge = self.generate_challenge(self._verifier)

        self._callback_url = callback_url

    @classmethod
    def generate_verifier(cls) -> str:
        return urlsafe_unpadded_b64encode(secrets.token_bytes(32))

    @classmethod
    def generate_challenge(cls, verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode()).digest()
        return urlsafe_unpadded_b64encode(digest)

    @property
    def verifier(self) -> str:
        return self._verifier

    @property
    def challenge(self) -> str:
        return self._challenge

    @property
    def value(self) -> str:
        return self._future.result()

    @value.setter
    def value(self, value: str) -> None:
        self._future.set_result(value)

    @property
    def callback_url(self) -> URL:
        assert self._callback_url
        return self._callback_url

    @callback_url.setter
    def callback_url(self, value: URL) -> None:
        self._callback_url = value

    def cancel(self) -> None:
        self._future.cancel()

    async def wait(self, timeout_s: float = 60.0) -> str:
        try:
            await asyncio.wait_for(self._future, timeout_s)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            raise AuthException("failed to get an authorization code")
        return self.value


@dataclass(frozen=True)
class AuthToken:
    token: str
    expiration_time: int
    refresh_token: str

    time_factory: Callable[..., float] = time.time

    @property
    def is_expired(self) -> bool:
        current_time = int(self.time_factory())
        return self.expiration_time <= current_time

    @classmethod
    def create(
        cls,
        token: str,
        expires_in: int,
        refresh_token: str,
        expiration_ratio: float = 0.75,
        time_factory: Optional[Callable[..., float]] = None,
    ) -> "AuthToken":
        time_factory = time_factory or cls.time_factory
        expiration_time = int(time_factory()) + int(expires_in * expiration_ratio)
        return cls(
            token=token,
            expiration_time=expiration_time,
            refresh_token=refresh_token,
            time_factory=time_factory,
        )


class AuthTokenClient:
    def __init__(self, url: URL, client_id: str) -> None:
        self._url = url
        self._client_id = client_id

        self._client = ClientSession()

    async def close(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> "TokenClient":
        return self

    async def __aexit__(self, *_: Sequence[Any]) -> None:
        await self.close()

    async def request(self, code: AuthCode) -> AuthToken:
        payload = dict(
            grant_type="authorization_code",
            code_verifier=code.verifier,
            code=code.value,
            client_id=self._client_id,
            redirect_uri=str(code.callback_url),
        )
        async with self._client.post(self._url, json=payload) as resp:
            try:
                resp.raise_for_status()
            except ClientResponseError as exc:
                raise AuthException("failed to get an access token.") from exc
            resp_payload = await resp.json()
            return AuthToken.create(
                token=resp_payload["access_token"],
                expires_in=resp_payload["expires_in"],
                refresh_token=resp_payload["refresh_token"],
            )

    async def refresh(self, token: AuthToken) -> AuthToken:
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
            return AuthToken.create(
                token=resp_payload["access_token"],
                expires_in=resp_payload["expires_in"],
                refresh_token=token.refresh_token,
            )


class AuthCodeCallbackHandler:
    def __init__(self, code: AuthCode) -> None:
        self._code = code

    async def handle(self, request: Request) -> Response:
        code = request.query.get("code")

        if not code:
            self._code.cancel()
            raise HTTPBadRequest(text="The 'code' query parameter is missing.")

        self._code.value = code
        return Response(text="OK")


def create_auth_code_app(code: AuthCode) -> Application:
    app = Application()
    handler = AuthCodeCallbackHandler(code)
    app.router.add_get("/", handler.handle)
    return app


@asynccontextmanager
async def create_app_server_once(
    app: Application, *, host: str = "localhost", port: int = 8080
) -> AsyncIterator[URL]:
    try:
        runner = AppRunner(app)
        await runner.setup()
        site = TCPSite(runner, host, port)
        await site.start()
        yield URL(site.name)
    finally:
        await runner.cleanup()


@asynccontextmanager
async def create_app_server(
    app: Application, *, host: str = "localhost", ports: Sequence[int] = (8080,)
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
class AuthConfig:
    auth_url: URL
    token_url: URL

    client_id: str
    audience: str

    callback_urls: Sequence[URL] = (
        URL("http://localhost:54540"),
        URL("http://localhost:54541"),
        URL("http://localhost:54542"),
    )

    @property
    def callback_host(self) -> str:
        return self.callback_urls[0].host

    @property
    def callback_ports(self) -> List[int]:
        return [url.port for url in self.callback_urls]

    @classmethod
    def create(cls, base_url: URL, client_id: str, audience: str) -> "AuthConfig":
        return cls(
            auth_url=base_url.with_path("/authorize"),
            token_url=base_url.with_path("/oauth/token"),
            client_id=client_id,
            audience=audience,
        )

    def combine_auth_url(self, code: AuthCode) -> URL:
        return self.auth_url.with_query(
            response_type="code",
            code_challenge=code.challenge,
            code_challenge_method="S256",
            client_id=self.client_id,
            redirect_uri=str(code.callback_url),
            scope="offline_access",
            audience=self.audience,
        )


class AuthCodeCallbackClient(abc.ABC):
    def __init__(self, url: URL) -> None:
        self._url = url

    @abc.abstractmethod
    async def request(self) -> None:
        pass


class AuthCodeCallbackWebBrowser(AuthCodeCallbackClient):
    async def request(self) -> None:
        webbrowser.open_new(str(self._url))


class AuthNegotiator:
    def __init__(
        self,
        config: AuthConfig,
        code_callback_client_factory: Callable[
            [URL], AuthCodeCallbackClient
        ] = AuthCodeCallbackWebBrowser,
    ) -> None:
        self._config = config
        self._code_callback_client_factory = code_callback_client_factory

    async def get_code(self) -> AuthCode:
        code = AuthCode()
        app = create_auth_code_app(code)

        async with create_app_server(
            app, host=self._config.callback_host, ports=self._config.callback_ports
        ) as url:
            code.callback_url = url

            auth_url = self._config.combine_auth_url(code=code)
            await self._code_callback_client_factory(auth_url).request()

            await code.wait()
        return code

    async def refresh_token(self, token: Optional[AuthToken] = None) -> AuthToken:
        async with AuthTokenClient(
            url=self._config.token_url, client_id=self._config.client_id
        ) as token_client:
            if not token:
                code = await self.get_code()
                return await token_client.request(code)

            if token.is_expired:
                return await token_client.refresh(token)

            return token


async def run(config: AuthConfig) -> None:
    negotiator = AuthNegotiator(config=config)
    token = await negotiator.refresh_token()
    print(token)


def main() -> None:
    config = AuthConfig.create(
        base_url=URL("https://dev-neuromation.auth0.com"),
        client_id="V7Jz87W9lhIlo0MyD0O6dufBvcXwM4DR",
        audience="https://platform.dev.neuromation.io",
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(config))


if __name__ == "__main__":
    main()
