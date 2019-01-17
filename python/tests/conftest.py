import pytest
from jose import jwt


@pytest.fixture
def token():
    return jwt.encode({"identity": "user"}, "secret", algorithm="HS256")


def setup_null_keyring(tmpdir, monkeypatch):
    import keyring.backends.null

    stored_keyring = keyring.get_keyring()
    keyring.set_keyring(keyring.backends.null.Keyring())
    yield

    keyring.set_keyring(stored_keyring)


@pytest.fixture
def run(request, monkeypatch, capsys, tmp_path, setup_null_keyring):
    import sys

    monkeypatch.setenv("HOME", str(tmp_path))

    def _run(arguments, rc_text):
        tmp_path.joinpath(".nmrc").write_text(rc_text)

        monkeypatch.setattr(sys, "argv", ["nmc"] + arguments)

        from neuromation.cli import main

        return main(), capsys.readouterr()

    return _run
