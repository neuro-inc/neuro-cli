from typing import Any, Tuple
from uuid import uuid4

import pytest

from tests.e2e import Helper


@pytest.fixture
def test_uris(helper: Helper) -> Any:
    uris = [
        f"storage://{helper.username}/{uuid4()}",
        f"image://{helper.username}/{uuid4()}",
    ]
    yield uris

    uri, uri2 = uris
    another_test_user = "test2"

    permissions = ((uri, "public"), (uri2, another_test_user))

    for permission in permissions:
        try:
            helper.run_cli(["acl", "revoke", permission[0], permission[1]])
        except SystemExit:  # let's ignore any possible errors
            pass


@pytest.mark.e2e
def test_grant_complete_lifecycle(helper: Helper, test_uris: Tuple[str, str]) -> None:
    uri, uri2 = test_uris

    another_test_user = "test2"

    captured = helper.run_cli(["acl", "grant", uri, "public", "read"])
    assert captured.out == ""
    expected_err = f"Using resource '{uri}'"
    assert expected_err in captured.err

    captured = helper.run_cli(["acl", "grant", uri2, another_test_user, "write"])
    assert captured.out == ""
    expected_err2 = f"Using resource '{uri2}'"
    assert expected_err2 in captured.err

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
    assert f"{uri} read public" in result
    assert f"{uri2} write {another_test_user}" in result
    for line in result:
        assert not line.startswith("storage://{helper.username} ")
        assert not line.endswith(f" {helper.username}")

    captured = helper.run_cli(["acl", "list", "--shared", "--scheme", "storage"])
    assert captured.err == ""
    result = captured.out.splitlines()
    assert f"{uri} read public" in result
    for line in result:
        assert line.startswith("storage://")
        assert not line.startswith("storage://{helper.username} ")
        assert not line.endswith(f" {helper.username}")

    captured = helper.run_cli(["acl", "list", "--shared", "--scheme", "image"])
    assert captured.err == ""
    result = captured.out.splitlines()
    assert f"{uri2} write {another_test_user}" in result
    for line in result:
        assert line.startswith("image://")
        assert not line.endswith(f" {helper.username}")

    captured = helper.run_cli(["acl", "revoke", uri, "public"])
    assert captured.out == ""
    assert expected_err in captured.err

    captured = helper.run_cli(["acl", "revoke", uri2, another_test_user])
    assert captured.out == ""
    assert expected_err2 in captured.err

    captured = helper.run_cli(["acl", "list", "--shared"])
    assert captured.err == ""
    result = captured.out.splitlines()
    assert f"{uri} read public" not in result
    assert f"{uri2} write {another_test_user}" not in result
    for line in result:
        assert not line.startswith("{uri} ")
        assert not line.startswith("{uri2} ")


@pytest.mark.e2e
def test_revoke_no_effect(helper: Helper) -> None:
    uri = f"storage://{helper.username}/{uuid4()}"
    with pytest.raises(SystemExit) as cm:
        helper.run_cli(["acl", "revoke", uri, "public"])
    assert cm.value.code == 127
    captured = helper.get_last_output()
    expected_out = "Operation has no effect."
    assert expected_out in captured.out
    expected_err = f"Using resource '{uri}'"
    assert expected_err in captured.err


@pytest.mark.e2e
def test_grant_image_no_tag(helper: Helper) -> None:
    rel_path = str(uuid4())
    rel_uri = f"image:{rel_path}"
    uri = f"image://{helper.username}/{rel_path}"
    another_test_user = "test2"
    captured = helper.run_cli(["acl", "grant", rel_uri, another_test_user, "read"])
    assert captured.out == ""
    expected_err = f"Using resource '{uri}'"
    assert expected_err in captured.err

    captured = helper.run_cli(["acl", "revoke", rel_uri, another_test_user])
    assert captured.out == ""
    assert expected_err in captured.err


@pytest.mark.e2e
def test_grant_image_with_tag_fails(helper: Helper) -> None:
    uri = f"image://{helper.username}/{uuid4()}:latest"
    another_test_user = "test2"
    with pytest.raises(SystemExit) as cm:
        helper.run_cli(["acl", "grant", uri, another_test_user, "read"])
    assert cm.value.code == 127
    last_out = helper.get_last_output().out
    assert "tag is not allowed" in last_out
