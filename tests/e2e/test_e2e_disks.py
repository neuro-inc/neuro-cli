from typing import Callable, ContextManager

import pytest

from tests.e2e.conftest import Helper


@pytest.mark.e2e
def test_create_get_list_delete(
    helper: Helper, disk_factory: Callable[[str], ContextManager[str]]
) -> None:
    cap = helper.run_cli(["disk", "ls"])
    assert cap.err == ""

    with disk_factory("2G") as disk_id:
        cap = helper.run_cli(["disk", "ls"])
        assert cap.err == ""
        assert disk_id in cap.out

        cap = helper.run_cli(["-q", "disk", "ls"])
        assert cap.err == ""
        assert disk_id in cap.out.splitlines()

        cap = helper.run_cli(["disk", "get", disk_id])
        assert cap.err == ""
        assert disk_id in cap.out
        assert "2.0G" in cap.out

    cap = helper.run_cli(["disk", "ls"])
    assert cap.err == ""
    assert disk_id not in cap.out
