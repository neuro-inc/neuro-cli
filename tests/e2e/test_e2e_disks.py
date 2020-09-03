import pytest

from tests.e2e.conftest import Helper


@pytest.mark.e2e
def test_create_get_list_delete(helper: Helper) -> None:
    cap = helper.run_cli(["disk", "ls"])
    assert cap.err == ""

    cap = helper.run_cli(["disk", "create", "2Gi"])
    assert cap.err == ""
    disk_id, *_ = cap.out.splitlines()[1].split()

    cap = helper.run_cli(["disk", "ls"])
    assert cap.err == ""
    assert disk_id in cap.out

    cap = helper.run_cli(["disk", "get", disk_id])
    assert cap.err == ""
    assert disk_id in cap.out
    assert "2Gi" in cap.out

    cap = helper.run_cli(["disk", "rm", disk_id])
    assert cap.err == ""

    cap = helper.run_cli(["disk", "ls"])
    assert cap.err == ""
    assert disk_id not in cap.out
