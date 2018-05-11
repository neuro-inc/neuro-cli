import pytest
from neuromation import Model


@pytest.fixture
def model(loop):
    return Model(url='http://127.0.0.1')
