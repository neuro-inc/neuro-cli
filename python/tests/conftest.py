from unittest.mock import MagicMock, Mock

import pytest

from neuromation.client.jobs import ResourceSharing
from neuromation.client.storage import Storage


@pytest.fixture(scope="function")
def storage(loop):
    storage = Storage(url="http://127.0.0.1", token="test-token-for-storage", loop=loop)
    yield storage
    loop.run_until_complete(storage.close())


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
def http_storage(loop):
    storage = Storage(url="http://127.0.0.1", token="test-token-for-storage", loop=loop)
    return storage


@pytest.fixture(scope="function")
def http_backed_storage(http_storage):
    def partial_mocked_store():
        return http_storage

    return partial_mocked_store


@pytest.fixture
def setup_local_keyring(tmpdir, monkeypatch):

    import keyring
    import keyrings.cryptfile.file
    import keyrings.cryptfile.file_base

    def file_path():
        return str(tmpdir / "keystore")

    stored_keyring = keyring.get_keyring()
    keyring.set_keyring(keyrings.cryptfile.file.PlaintextKeyring())
    monkeypatch.setattr(
        keyrings.cryptfile.file_base.FileBacked, "file_path", file_path()
    )
    yield

    keyring.set_keyring(stored_keyring)


@pytest.fixture
def run(request, monkeypatch, capsys, tmpdir, setup_local_keyring):
    import sys
    from pathlib import Path

    def _home():
        return Path(tmpdir)

    def _run(arguments, rc_text):
        tmpdir.join(".nmrc").open("w").write(rc_text)

        monkeypatch.setattr(Path, "home", _home)
        monkeypatch.setattr(sys, "argv", ["nmc"] + arguments)

        from neuromation.cli import main

        return main(), capsys.readouterr()

    return _run
