import pytest
from jose import jwt
from yarl import URL

from neuromation.api import Client
from neuromation.api.config import _AuthConfig, _AuthToken, _Config, _PyPIVersion


@pytest.fixture
def token():
    return jwt.encode({"identity": "user"}, "secret", algorithm="HS256")


@pytest.fixture
def auth_config():
    return _AuthConfig.create(
        auth_url=URL("https://dev-neuromation.auth0.com/authorize"),
        token_url=URL("https://dev-neuromation.auth0.com/oauth/token"),
        client_id="CLIENT-ID",
        audience="https://platform.dev.neuromation.io",
        success_redirect_url="https://neu.ro/#running-your-first-job",
        callback_urls=[
            URL("http://127.0.0.1:54540"),
            URL("http://127.0.0.1:54541"),
            URL("http://127.0.0.1:54542"),
        ],
    )


@pytest.fixture
def make_client(token, auth_config):
    def go(url, registry_url=""):
        config = _Config(
            auth_config=auth_config,
            auth_token=_AuthToken.create_non_expiring(token),
            pypi=_PyPIVersion.create_uninitialized(),
            url=URL(url),
            registry_url=URL(registry_url),
        )
        return Client(config)

    return go
