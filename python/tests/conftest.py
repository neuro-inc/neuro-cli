from unittest.mock import MagicMock, Mock

import pytest

from neuromation import Job, Model, Storage
from neuromation.client.jobs import ResourceSharing


@pytest.fixture
def model(loop):
    model = Model(url="http://127.0.0.1", token="test-token-for-model", loop=loop)
    yield model
    loop.run_until_complete(model.close())


@pytest.fixture(scope="function")
def storage(loop):
    storage = Storage(url="http://127.0.0.1", token="test-token-for-storage", loop=loop)
    yield storage
    loop.run_until_complete(storage.close())


@pytest.fixture
def jobs(loop):
    job = Job(url="http://127.0.0.1", token="test-token-for-job", loop=loop)
    yield job
    loop.run_until_complete(job.close())


@pytest.fixture
def resource_sharing(loop):
    resource_sharing = ResourceSharing(
        url="http://127.0.0.1", token="test-token-for-job", loop=loop
    )
    yield resource_sharing
    loop.run_until_complete(resource_sharing.close())


@pytest.fixture(scope="function")
def mocked_store(loop):
    my_mock = MagicMock(Storage("no-url", "no-token", loop=loop))
    my_mock.__enter__ = Mock(return_value=my_mock)
    my_mock.__exit__ = Mock(return_value=False)
    return my_mock


@pytest.fixture(scope="function")
def mocked_model(loop):
    my_mock = MagicMock(Model("no-url", "no-token", loop=loop))
    my_mock.__enter__ = Mock(return_value=my_mock)
    my_mock.__exit__ = Mock(return_value=False)
    return my_mock


@pytest.fixture(scope="function")
def mocked_jobs(loop):
    my_mock = MagicMock(Job("no-url", "no-token", loop=loop))
    my_mock.__enter__ = Mock(return_value=my_mock)
    my_mock.__exit__ = Mock(return_value=False)
    return my_mock


@pytest.fixture(scope="function")
def mocked_resource_share(loop):
    my_mock = MagicMock(ResourceSharing("no-url", "no-token", loop=loop))
    my_mock.__enter__ = Mock(return_value=my_mock)
    my_mock.__exit__ = Mock(return_value=False)
    return my_mock


@pytest.fixture(scope="function")
def partial_mocked_store(mocked_store):
    def partial_mocked_store_func():
        return mocked_store

    return partial_mocked_store_func


@pytest.fixture(scope="function")
def partial_mocked_model(mocked_model):
    def partial_mocked_model_func():
        return mocked_model

    return partial_mocked_model_func


@pytest.fixture(scope="function")
def partial_mocked_job(mocked_jobs):
    def partial_mocked_jobs_func():
        return mocked_jobs

    return partial_mocked_jobs_func


@pytest.fixture(scope="function")
def partial_mocked_resource_share(mocked_resource_share):
    def partial_mocked_resource_share_func():
        return mocked_resource_share

    return partial_mocked_resource_share_func


@pytest.fixture(scope="function")
def http_storage(loop):
    storage = Storage(url="http://127.0.0.1", token="test-token-for-storage", loop=loop)
    return storage


@pytest.fixture(scope="function")
def http_backed_storage(http_storage):
    def partial_mocked_store():
        return http_storage

    return partial_mocked_store
