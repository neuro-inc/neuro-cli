import pytest

from tests.e2e import Helper


@pytest.mark.e2e
def test_share_complete_lifecycle(helper: Helper) -> None:
    captured = helper.run_cli(["share", "storage:shared-read", "public", "read"])
    assert captured.out == ""
    expected_err = f"Using resource 'storage://{helper.username}/shared-read'"
    assert expected_err in captured.err

    captured = helper.run_cli(["revoke", "storage:shared-read", "public"])
    assert captured.out == ""
    assert expected_err in captured.err


@pytest.mark.e2e
def test_unshare_no_effect(helper: Helper) -> None:
    with pytest.raises(SystemExit) as cm:
        helper.run_cli(["revoke", "storage:unshared", "public"])
    assert cm.value.code == 127
    captured = helper.get_last_output()
    expected_out = "Operation has no effect."
    assert expected_out in captured.out
    expected_err = f"Using resource 'storage://{helper.username}/unshared'"
    assert expected_err in captured.err


@pytest.mark.e2e
def test_share_image_no_tag(helper: Helper) -> None:
    another_test_user = "test2"
    captured = helper.run_cli(["share", "image:my-ubuntu", another_test_user, "read"])
    assert captured.out == ""
    expected_err = f"Using resource 'image://{helper.username}/my-ubuntu'"
    assert expected_err in captured.err

    captured = helper.run_cli(["revoke", "image:my-ubuntu", another_test_user])
    assert captured.out == ""
    assert expected_err in captured.err


@pytest.mark.e2e
def test_share_image_with_tag_fails(helper: Helper) -> None:
    another_test_user = "test2"
    with pytest.raises(SystemExit) as cm:
        helper.run_cli(
            ["share", "image://~/my-ubuntu:latest", another_test_user, "read"]
        )
    assert cm.value.code == 127
    last_out = helper.get_last_output().out
    assert "tag is not allowed" in last_out
