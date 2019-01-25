import pytest
from jose import jwt

from neuromation.cli import main


@pytest.fixture
def token():
    return jwt.encode({"identity": "user"}, "secret", algorithm="HS256")


@pytest.fixture
def setup_null_keyring():
    import keyring.backends.null

    stored_keyring = keyring.get_keyring()
    keyring.set_keyring(keyring.backends.null.Keyring())
    yield

    keyring.set_keyring(stored_keyring)


@pytest.fixture
def run(request, monkeypatch, capsys, tmp_path, setup_null_keyring):
    monkeypatch.setenv("HOME", str(tmp_path))

    def _run(arguments, rc_text):
        tmp_path.joinpath(".nmrc").write_text(rc_text)

        return main(["neuro"] + arguments), capsys.readouterr()

    return _run
