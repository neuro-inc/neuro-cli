import pytest


@pytest.mark.e2e
def test_share_complete_lifecycle(helper):
    captured = helper.run_cli(["share", "storage:shared-read", "public", "read"])
    assert captured.out == ""
    captured = helper.run_cli(["revoke", "storage:///shared-read", "public"])
    assert captured.out == ""
    captured = helper.run_cli(["share", "storage:shared-read", "public", "read"])
    assert captured.out == ""
