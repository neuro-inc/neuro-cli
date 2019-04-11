import pytest
from jose import jwt

from yarl import URL

from neuromation.api import Client
from neuromation.api.config import _AuthConfig, _AuthToken, _Config, _PyPIVersion



@pytest.fixture
def token():
    return jwt.encode({"identity": "user"}, "secret", algorithm="HS256")


@pytest.fixture
def make_client(token):
    def go(url, registry_url=""):
        config = _Config(
            auth_config=_AuthConfig.create_uninitialized(),
            auth_token=_AuthToken.create_non_expiring(token),
            pypi=_PyPIVersion.create_uninitialized(),
            url=URL(url),
            registry_url=URL(registry_url),
        )
        return Client(config)

    return go
