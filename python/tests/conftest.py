import pytest
from jose import jwt


@pytest.fixture
def token():
    return jwt.encode({"identity": "user"}, "secret", algorithm="HS256")
