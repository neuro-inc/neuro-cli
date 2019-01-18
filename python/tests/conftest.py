import pytest
from jose import jwt


@pytest.fixture
def token():
    return jwt.encode({"identity": "user"}, "secret", algorithm="HS256")


@pytest.fixture
def setup_local_keyring(tmp_path, monkeypatch):

    import keyring
    import keyrings.cryptfile.file
    import keyrings.cryptfile.file_base

    def file_path():
        return str(tmp_path / "keystore")

    stored_keyring = keyring.get_keyring()
    keyring.set_keyring(keyrings.cryptfile.file.PlaintextKeyring())
    monkeypatch.setattr(
        keyrings.cryptfile.file_base.FileBacked, "file_path", file_path()
    )
    yield

    keyring.set_keyring(stored_keyring)


@pytest.fixture
def run(request, monkeypatch, capsys, tmp_path, setup_local_keyring):
    import sys

    monkeypatch.setenv("HOME", str(tmp_path))

    def _run(arguments, rc_text):
        tmp_path.joinpath(".nmrc").write_text(rc_text)

        monkeypatch.setattr(sys, "argv", ["nmc"] + arguments)

        from neuromation.cli import main

        return main(), capsys.readouterr()

    return _run
