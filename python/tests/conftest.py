import pytest
from jose import jwt

from neuromation.cli import main


@pytest.fixture
def token():
    return jwt.encode({"identity": "user"}, "secret", algorithm="HS256")


@pytest.fixture
def run(request, monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    def _run(arguments, rc_text):
        tmp_path.joinpath(".nmrc").write_text(rc_text)

        return main(["neuro"] + arguments), capsys.readouterr()

    return _run
