import asyncio
from typing import AsyncIterator
from unittest import mock

import pytest
from aiohttp import ClientSession
from aiohttp.test_utils import TestServer as _TestServer
from aiohttp.web import (
    Application,
    HTTPBadRequest,
    HTTPForbidden,
    HTTPFound,
    HTTPOk,
    Request,
    Response,
    json_response,
)
from yarl import URL

from neuromation.cli.login import (
    AuthCode,
    AuthCodeCallbackClient,
    AuthConfig,
    AuthException,
    AuthNegotiator,
    AuthToken,
    AuthTokenClient,
    create_app_server,
    create_app_server_once,
    create_auth_code_app,
)


class TestAuthCode:
    async def test_wait_timed_out(self) -> None:
        code = AuthCode()
        with pytest.raises(AuthException, match="failed to get an authorization code"):
            await code.wait(timeout_s=0.0)

    async def test_wait_cancelled(self) -> None:
        code = AuthCode()
        code.cancel()
        with pytest.raises(AuthException, match="failed to get an authorization code"):
            await code.wait()

    async def test_wait(self) -> None:
        code = AuthCode()
        code.value = "testcode"
        value = await code.wait()
        assert value == "testcode"


class TestAuthToken:
    def test_is_not_expired(self) -> None:
        token = AuthToken.create(
            token="test_token",
            expires_in=100,
            refresh_token="test_refresh_token",
            time_factory=lambda: 2000.0,
        )
        assert token.token == "test_token"
        assert token.expiration_time == 2075
        assert not token.is_expired
        assert token.refresh_token == "test_refresh_token"

    def test_is_expired(self) -> None:
        token = AuthToken.create(
            token="test_token",
            expires_in=0,
            refresh_token="test_refresh_token",
            time_factory=lambda: 2000.0,
        )
        assert token.token == "test_token"
        assert token.expiration_time == 2000
        assert token.is_expired
        assert token.refresh_token == "test_refresh_token"


class TestAuthCodeApp:
    @pytest.fixture
    async def client(
        self, loop: asyncio.AbstractEventLoop
    ) -> AsyncIterator[ClientSession]:
        async with ClientSession() as client:
            yield client

    async def assert_code_callback_success(
        self, code: AuthCode, client: ClientSession, url: URL
    ) -> None:
        async with client.get(url, params={"code": "testcode"}) as resp:
            assert resp.status == HTTPOk.status_code
            text = await resp.text()
            assert text == "OK"

        assert code.value == "testcode"

    async def assert_code_callback_failure(
        self, code: AuthCode, client: ClientSession, url: URL
    ) -> None:
        async with client.get(url) as resp:
            assert resp.status == HTTPBadRequest.status_code
            text = await resp.text()
            assert text == "The 'code' query parameter is missing."

        with pytest.raises(asyncio.CancelledError):
            code.value

    async def test_create_app_server_once(self, client: ClientSession) -> None:
        code = AuthCode()
        app = create_auth_code_app(code)

        async with create_app_server_once(app, host="localhost", port=54540) as url:
            assert url == URL("http://localhost:54540")
            await self.assert_code_callback_success(code, client, url)

    async def test_create_app_server_once_failure(self, client: ClientSession) -> None:
        code = AuthCode()
        app = create_auth_code_app(code)

        async with create_app_server_once(app, host="localhost", port=54540) as url:
            assert url == URL("http://localhost:54540")
            await self.assert_code_callback_failure(code, client, url)

    async def test_create_app_server(self, client: ClientSession) -> None:
        code = AuthCode()
        app = create_auth_code_app(code)

        async with create_app_server(app, host="localhost", ports=[54540]) as url:
            assert url == URL("http://localhost:54540")
            await self.assert_code_callback_success(code, client, url)

    async def test_create_app_server_no_ports(self) -> None:
        code = AuthCode()
        app = create_auth_code_app(code)

        async with create_app_server_once(app, host="localhost", port=54540):
            with pytest.raises(RuntimeError, match="No free ports."):
                async with create_app_server(app, ports=[54540]):
                    pass

    async def test_create_app_server_port_conflict(self, client: ClientSession) -> None:
        code = AuthCode()
        app = create_auth_code_app(code)
        async with create_app_server(app, ports=[54540, 54541]) as url:
            assert url == URL("http://localhost:54540")
            async with create_app_server(app, ports=[54540, 54541]) as url:
                assert url == URL("http://localhost:54541")
                await self.assert_code_callback_success(code, client, url)


class _TestAuthHandler:
    def __init__(self, client_id: str) -> None:
        self._client_id = client_id

        self._code = "test_code"
        self._token = "test_access_token"
        self._token_refreshed = "test_access_token_refreshed"
        self._refresh_token = "test_refresh_token"
        self._token_expires_in = 1234

    async def handle_authorize(self, request: Request) -> Response:
        # TODO: assert query
        url = URL(request.query["redirect_uri"]).with_query(code=self._code)
        raise HTTPFound(url)

    async def handle_token(self, request: Request) -> Response:
        payload = await request.json()
        grant_type = payload["grant_type"]
        if grant_type == "authorization_code":
            assert payload == dict(
                grant_type="authorization_code",
                code_verifier=mock.ANY,
                code=self._code,
                client_id=self._client_id,
                redirect_uri=mock.ANY,
            )
            resp_payload = dict(
                access_token=self._token,
                expires_in=self._token_expires_in,
                refresh_token=self._refresh_token,
            )
        else:
            assert payload == dict(
                grant_type="refresh_token",
                refresh_token=self._refresh_token,
                client_id=self._client_id,
            )
            resp_payload = dict(
                access_token=self._token_refreshed, expires_in=self._token_expires_in
            )
        return json_response(resp_payload)


@pytest.fixture
def auth_client_id() -> str:
    return "test_client_id"


@pytest.fixture
async def auth_server(auth_client_id, aiohttp_server) -> AsyncIterator[URL]:
    handler = _TestAuthHandler(client_id=auth_client_id)
    app = Application()
    app.router.add_get("/authorize", handler.handle_authorize)
    app.router.add_post("/oauth/token", handler.handle_token)
    server = await aiohttp_server(app)
    yield server.make_url("/")


@pytest.fixture
async def auth_config(
    auth_client_id: str, auth_server: URL
) -> AsyncIterator[AuthConfig]:
    yield AuthConfig.create(
        base_url=auth_server,
        client_id=auth_client_id,
        audience="https://platform.dev.neuromation.io",
    )


class TestTokenClient:
    async def test_request(self, auth_client_id: str, auth_config: AuthConfig) -> None:
        code = AuthCode()
        code.value = "test_code"
        code.callback_url = URL("http://localhost:54540")

        async with AuthTokenClient(
            auth_config.token_url, client_id=auth_client_id
        ) as client:
            token = await client.request(code)
            assert token.token == "test_access_token"
            assert token.refresh_token == "test_refresh_token"
            assert not token.is_expired

    async def test_refresh(self, auth_client_id: str, auth_config: AuthConfig) -> None:
        token = AuthToken.create(
            token="test_access_token",
            expires_in=1234,
            refresh_token="test_refresh_token",
        )

        async with AuthTokenClient(
            auth_config.token_url, client_id=auth_client_id
        ) as client:
            new_token = await client.refresh(token)
            assert new_token.token == "test_access_token_refreshed"
            assert new_token.refresh_token == "test_refresh_token"
            assert not token.is_expired

    async def test_forbidden(self, aiohttp_server: _TestServer) -> None:
        code = AuthCode()
        code.callback_url = "http://localhost:54540"
        code.value = "testcode"

        client_id = "test_client_id"

        async def handle_token(request: Request) -> Response:
            raise HTTPForbidden()

        app = Application()
        app.router.add_post("/oauth/token", handle_token)

        server = await aiohttp_server(app)
        url = server.make_url("/oauth/token")

        async with AuthTokenClient(url, client_id=client_id) as client:
            with pytest.raises(AuthException, match="failed to get an access token."):
                await client.request(code)

            with pytest.raises(AuthException, match="failed to get an access token."):
                token = AuthToken.create(
                    token="test_token",
                    expires_in=1234,
                    refresh_token="test_refresh_token",
                )
                await client.refresh(token)


class _TestAuthCodeCallbackClient(AuthCodeCallbackClient):
    async def request(self) -> None:
        async with ClientSession() as client:
            await client.get(self._url, allow_redirects=True)


class TestAuthNegotiator:
    async def test_get_code(self, auth_config: AuthConfig) -> None:
        negotiator = AuthNegotiator(
            config=auth_config, code_callback_client_factory=_TestAuthCodeCallbackClient
        )
        code = await negotiator.get_code()
        assert code.value == "test_code"
        assert code.callback_url == URL("http://localhost:54540")

    async def test_get_token(self, auth_config: AuthConfig) -> None:
        negotiator = AuthNegotiator(
            config=auth_config, code_callback_client_factory=_TestAuthCodeCallbackClient
        )
        token = await negotiator.refresh_token(token=None)
        assert token.token == "test_access_token"
        assert token.refresh_token == "test_refresh_token"

    async def test_refresh_token_noop(self, auth_config: AuthConfig) -> None:
        negotiator = AuthNegotiator(
            config=auth_config, code_callback_client_factory=_TestAuthCodeCallbackClient
        )
        token = await negotiator.refresh_token(token=None)
        assert token.token == "test_access_token"
        assert token.refresh_token == "test_refresh_token"
        assert not token.is_expired

        token = await negotiator.refresh_token(token=token)
        assert token.token == "test_access_token"
        assert token.refresh_token == "test_refresh_token"

    async def test_refresh_token(self, auth_config: AuthConfig) -> None:
        negotiator = AuthNegotiator(
            config=auth_config, code_callback_client_factory=_TestAuthCodeCallbackClient
        )
        token = await negotiator.refresh_token(token=None)
        assert token.token == "test_access_token"
        assert token.refresh_token == "test_refresh_token"
        assert not token.is_expired

        token = AuthToken.create(
            token=token.token, expires_in=0, refresh_token=token.refresh_token
        )
        token = await negotiator.refresh_token(token=token)
        assert token.token == "test_access_token_refreshed"
        assert token.refresh_token == "test_refresh_token"
