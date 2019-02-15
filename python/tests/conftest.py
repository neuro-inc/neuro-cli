import pytest
from jose import jwt

from neuromation.cli import main


@pytest.fixture
def token():
    return jwt.encode({"identity": "user"}, "secret", algorithm="HS256")
