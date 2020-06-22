import uuid

import pytest

from tests.e2e.conftest import Helper


@pytest.fixture
def secret_name() -> str:
    return "secret" + str(uuid.uuid4()).replace("-", "")[:10]


@pytest.mark.e2e
def test_create_list_delete(helper: Helper, secret_name: str) -> None:
    cap = helper.run_cli(["secret", "ls"])
    assert cap.err == ""
    assert secret_name not in cap.out

    cap = helper.run_cli(["secret", "add", secret_name, "value"])
    assert cap.err == ""

    cap = helper.run_cli(["secret", "ls"])
    assert cap.err == ""
    assert secret_name in cap.out

    cap = helper.run_cli(["secret", "rm", secret_name])
    assert cap.err == ""

    cap = helper.run_cli(["secret", "ls"])
    assert cap.err == ""
    assert secret_name not in cap.out
