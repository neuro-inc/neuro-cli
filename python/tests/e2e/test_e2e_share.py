import pytest


@pytest.mark.e2e
def test_share_complete_lifecycle(run):
    captured = run(["share", "storage:shared-read", "public", "read"])
    assert captured.out.strip() == ""
    # TODO: Add revoke here
