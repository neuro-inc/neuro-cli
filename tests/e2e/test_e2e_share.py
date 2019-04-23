import pytest


@pytest.mark.e2e
def test_share_complete_lifecycle(helper):
    captured = helper.run_cli(["share", "storage:shared-read", "public", "read"])
    expected_err = f"Using resource 'storage://{helper.username}/shared-read'"
    assert expected_err in captured.err
    assert captured.out == ""
    captured = helper.run_cli(["revoke", "storage://shared-read", "public"])
    assert captured.out == ""
    captured = helper.run_cli(["share", "storage:shared-read", "public", "read"])
    assert captured.out == ""


@pytest.mark.e2e
def test_share_image_no_tag(helper):
    another_test_user = "test2"
    captured = helper.run_cli(["share", "image:my-ubuntu", another_test_user, "read"])
    assert captured.out == ""
    expected_err = f"Using resource 'image://{helper.username}/my-ubuntu'"
    assert expected_err in captured.err
    # TODO: Add revoke here


@pytest.mark.e2e
def test_share_image_with_tag_fails(helper):
    another_test_user = "test2"
    with pytest.raises(SystemExit) as cm:
        helper.run_cli(
            ["share", "image://~/my-ubuntu:latest", another_test_user, "read"]
        )
    assert cm.value.code == 127
    last_out = helper.get_last_output().out
    assert "tag is not allowed" in last_out
