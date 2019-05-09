from uuid import uuid4

import pytest

from tests.e2e import Helper


@pytest.mark.e2e
def test_share_complete_lifecycle(helper: Helper) -> None:
    uri = f"storage://{helper.username}/{uuid4()}"
    captured = helper.run_cli(["share", uri, "public", "read"])
    assert captured.out == ""
    expected_err = f"Using resource '{uri}'"
    assert expected_err in captured.err

    captured = helper.run_cli(["revoke", uri, "public"])
    assert captured.out == ""
    assert expected_err in captured.err


@pytest.mark.e2e
def test_unshare_no_effect(helper: Helper) -> None:
    uri = f"storage://{helper.username}/{uuid4()}"
    with pytest.raises(SystemExit) as cm:
        helper.run_cli(["revoke", uri, "public"])
    assert cm.value.code == 127
    captured = helper.get_last_output()
    expected_out = "Operation has no effect."
    assert expected_out in captured.out
    expected_err = f"Using resource '{uri}'"
    assert expected_err in captured.err


@pytest.mark.e2e
def test_share_image_no_tag(helper: Helper) -> None:
    uri = f"image://{helper.username}/{uuid4()}"
    another_test_user = "test2"
    captured = helper.run_cli(["share", uri, another_test_user, "read"])
    assert captured.out == ""
    expected_err = f"Using resource '{uri}'"
    assert expected_err in captured.err

    captured = helper.run_cli(["revoke", uri, another_test_user])
    assert captured.out == ""
    assert expected_err in captured.err


@pytest.mark.e2e
def test_share_image_with_tag_fails(helper: Helper) -> None:
    uri = f"image://{helper.username}/{uuid4()}:latest"
    another_test_user = "test2"
    with pytest.raises(SystemExit) as cm:
        helper.run_cli(["share", uri, another_test_user, "read"])
    assert cm.value.code == 127
    last_out = helper.get_last_output().out
    assert "tag is not allowed" in last_out
