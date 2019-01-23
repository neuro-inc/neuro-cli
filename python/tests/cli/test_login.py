import asyncio

import pytest
from aiohttp import ClientSession
from aiohttp.web import (
    Application,
    HTTPBadRequest,
    HTTPForbidden,
    HTTPOk,
    Request,
    Response,
    json_response,
)
from yarl import URL

from neuromation.cli.login import (
    AuthCode,
    AuthException,
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
    def test_is_not_expired(self):
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

    def test_is_not_expired(self):
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
    async def client(self, loop) -> ClientSession:
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


class TestTokenClient:
    async def test_request(self, aiohttp_server) -> None:
        code = AuthCode()
        code.callback_url = "http://localhost:54540"
        code.value = "testcode"

        client_id = "test_client_id"

        async def handle_token(request: Request) -> Response:
            payload = await request.json()
            assert payload == dict(
                grant_type="authorization_code",
                code_verifier=code.verifier,
                code=code.value,
                client_id=client_id,
                redirect_uri=str(code.callback_url),
            )
            return json_response(
                dict(
                    access_token="test_access_token",
                    expires_in=1234,
                    refresh_token="test_refresh_token",
                )
            )

        app = Application()
        app.router.add_post("/oauth/token", handle_token)

        server = await aiohttp_server(app)
        url = server.make_url("/oauth/token")

        async with AuthTokenClient(url, client_id=client_id) as client:
            token = await client.request(code)
            assert token.token == "test_access_token"
            assert token.refresh_token == "test_refresh_token"
            assert not token.is_expired

    async def test_refresh(self, aiohttp_server) -> None:
        token = AuthToken.create(
            token="test_token", expires_in=1234, refresh_token="test_refresh_token"
        )

        client_id = "test_client_id"

        async def handle_token(request: Request) -> Response:
            payload = await request.json()
            assert payload == dict(
                grant_type="refresh_token",
                refresh_token=token.refresh_token,
                client_id=client_id,
            )
            return json_response(
                dict(access_token="test_access_token", expires_in=1234)
            )

        app = Application()
        app.router.add_post("/oauth/token", handle_token)

        server = await aiohttp_server(app)
        url = server.make_url("/oauth/token")

        async with AuthTokenClient(url, client_id=client_id) as client:
            new_token = await client.refresh(token)
            assert new_token.token == "test_access_token"
            assert new_token.refresh_token == "test_refresh_token"
            assert not token.is_expired

    async def test_forbidden(self, aiohttp_server) -> None:
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
