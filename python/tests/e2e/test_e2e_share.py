import pytest


@pytest.mark.e2e
def test_share_complete_lifecycle(run_cli):
    captured = run_cli(["share", "storage:shared-read", "public", "read"])
    assert captured.out.strip() == ""
    # TODO: Add revoke here
