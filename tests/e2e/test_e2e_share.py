import pytest

from tests.e2e import Helper


@pytest.mark.e2e
def test_grant_complete_lifecycle(helper: Helper) -> None:
    captured = helper.run_cli(["acl", "grant", "storage:shared-read", "public", "read"])
    assert captured.out == ""
    expected_err = f"Using resource 'storage://{helper.username}/shared-read'"
    assert expected_err in captured.err

    captured = helper.run_cli(["acl", "list"])
    assert captured.err == ""
    result = captured.out.splitlines()
    assert f"storage://{helper.username} manage" in result
    assert f"user://{helper.username} read" in result

    captured = helper.run_cli(["acl", "list", "--scheme", "storage"])
    assert captured.err == ""
    result = captured.out.splitlines()
    assert f"storage://{helper.username} manage" in result
    for line in result:
        assert line.startswith("storage://")

    captured = helper.run_cli(["acl", "list", "--shared"])
    assert captured.err == ""
    result = captured.out.splitlines()
    assert result == [f"storage://{helper.username}/shared-read read public"]

    captured = helper.run_cli(["acl", "list", "--shared", "--scheme", "storage"])
    assert captured.err == ""
    result = captured.out.splitlines()
    assert result == [f"storage://{helper.username}/shared-read read public"]

    captured = helper.run_cli(["acl", "list", "--shared", "--scheme", "image"])
    assert captured.err == ""
    result = captured.out.splitlines()
    assert result == []

    captured = helper.run_cli(["acl", "revoke", "storage:shared-read", "public"])
    assert captured.out == ""
    assert expected_err in captured.err

    captured = helper.run_cli(["acl", "list", "--shared"])
    assert captured.err == ""
    result = captured.out.splitlines()
    assert result == []


@pytest.mark.e2e
def test_revoke_no_effect(helper: Helper) -> None:
    with pytest.raises(SystemExit) as cm:
        helper.run_cli(["acl", "revoke", "storage:unshared", "public"])
    assert cm.value.code == 127
    captured = helper.get_last_output()
    expected_out = "Operation has no effect."
    assert expected_out in captured.out
    expected_err = f"Using resource 'storage://{helper.username}/unshared'"
    assert expected_err in captured.err


@pytest.mark.e2e
def test_grant_image_no_tag(helper: Helper) -> None:
    another_test_user = "test2"
    captured = helper.run_cli(
        ["acl", "grant", "image:my-ubuntu", another_test_user, "read"]
    )
    assert captured.out == ""
    expected_err = f"Using resource 'image://{helper.username}/my-ubuntu'"
    assert expected_err in captured.err

    captured = helper.run_cli(["acl", "revoke", "image:my-ubuntu", another_test_user])
    assert captured.out == ""
    assert expected_err in captured.err


@pytest.mark.e2e
def test_grant_image_with_tag_fails(helper: Helper) -> None:
    another_test_user = "test2"
    with pytest.raises(SystemExit) as cm:
        helper.run_cli(
            ["acl", "grant", "image://~/my-ubuntu:latest", another_test_user, "read"]
        )
    assert cm.value.code == 127
    last_out = helper.get_last_output().out
    assert "tag is not allowed" in last_out
