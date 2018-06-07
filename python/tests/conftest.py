import pytest

from neuromation import Model


@pytest.fixture
def model(loop):
    model = Model(url='http://127.0.0.1', loop=loop)
    yield model
    loop.run_until_complete(model.close())
