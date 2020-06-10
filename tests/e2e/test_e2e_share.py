import subprocess
from typing import Any
from uuid import uuid4

import pytest

from tests.e2e import Helper


def revoke(helper: Helper, uri: str, username: str) -> None:
    try:
        helper.run_cli(["acl", "revoke", uri, username])
    except subprocess.CalledProcessError:  # let's ignore any possible errors
        pass


@pytest.mark.e2e
def test_grant_complete_lifecycle(request: Any, helper: Helper) -> None:
    uri = f"storage://{helper.cluster_name}/{helper.username}/{uuid4()}"
    uri2 = f"image://{helper.cluster_name}/{helper.username}/{uuid4()}"

    another_test_user = "test2"

    request.addfinalizer(lambda: revoke(helper, uri, "public"))
    captured = helper.run_cli(["-v", "acl", "grant", uri, "public", "read"])
    assert captured.out == ""
    expected_err = f"Using resource '{uri}'"
    assert expected_err in captured.err

    request.addfinalizer(lambda: revoke(helper, uri2, another_test_user))
    captured = helper.run_cli(["-v", "acl", "grant", uri2, another_test_user, "write"])
    assert captured.out == ""
    expected_err2 = f"Using resource '{uri2}'"
    assert expected_err2 in captured.err

    captured = helper.run_cli(["-v", "acl", "list", "--full-uri"])
    assert captured.err == ""
    result = captured.out.splitlines()
    assert (
        f"storage://{helper.cluster_name}/{helper.username} manage" in result
        or f"storage://{helper.cluster_name} manage" in result
    )
    assert f"user://{helper.username} read" in result

    captured = helper.run_cli(
        ["-v", "acl", "list", "--full-uri", "--scheme", "storage"]
    )
    assert captured.err == ""
    result = captured.out.splitlines()
    assert (
        f"storage://{helper.cluster_name}/{helper.username} manage" in result
        or f"storage://{helper.cluster_name} manage" in result
    )
    for line in result:
        assert line.startswith("storage://")

    captured = helper.run_cli(["-v", "acl", "list", "--full-uri", "--shared"])
    assert captured.err == ""
    result = captured.out.splitlines()
    assert f"{uri} read public" in result
    assert f"{uri2} write {another_test_user}" in result
    for line in result:
        assert not line.endswith(f" {helper.username}")

    captured = helper.run_cli(
        ["-v", "acl", "list", "--full-uri", "--shared", "--scheme", "storage"]
    )
    assert captured.err == ""
    result = captured.out.splitlines()
    assert f"{uri} read public" in result
    for line in result:
        assert line.startswith("storage://")
        assert not line.endswith(f" {helper.username}")

    captured = helper.run_cli(
        ["-v", "acl", "list", "--full-uri", "--shared", "--scheme", "image"]
    )
    assert captured.err == ""
    result = captured.out.splitlines()
    assert f"{uri2} write {another_test_user}" in result
    for line in result:
        assert line.startswith("image://")
        assert not line.endswith(f" {helper.username}")

    captured = helper.run_cli(["-v", "acl", "revoke", uri, "public"])
    assert captured.out == ""
    assert expected_err in captured.err

    captured = helper.run_cli(["-v", "acl", "revoke", uri2, another_test_user])
    assert captured.out == ""
    assert expected_err2 in captured.err

    captured = helper.run_cli(["-v", "acl", "list", "--full-uri", "--shared"])
    assert captured.err == ""
    result = captured.out.splitlines()
    assert f"{uri} read public" not in result
    assert f"{uri2} write {another_test_user}" not in result
    for line in result:
        assert not line.startswith("{uri} ")
        assert not line.startswith("{uri2} ")


@pytest.mark.e2e
def test_revoke_no_effect(helper: Helper) -> None:
    uri = f"storage://{helper.cluster_name}/{helper.username}/{uuid4()}"
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(["-v", "acl", "revoke", uri, "public"])
    assert cm.value.returncode == 127
    assert "Operation has no effect" in cm.value.stderr
    assert f"Using resource '{uri}'" in cm.value.stderr


@pytest.mark.e2e
def test_grant_image_no_tag(request: Any, helper: Helper) -> None:
    rel_path = str(uuid4())
    rel_uri = f"image:{rel_path}"
    uri = f"image://{helper.cluster_name}/{helper.username}/{rel_path}"
    another_test_user = "test2"

    request.addfinalizer(lambda: revoke(helper, rel_uri, another_test_user))
    captured = helper.run_cli(
        ["-v", "acl", "grant", rel_uri, another_test_user, "read"]
    )
    assert captured.out == ""
    expected_err = f"Using resource '{uri}'"
    assert expected_err in captured.err

    captured = helper.run_cli(["-v", "acl", "revoke", rel_uri, another_test_user])
    assert captured.out == ""
    assert expected_err in captured.err


@pytest.mark.e2e
def test_grant_image_with_tag_fails(request: Any, helper: Helper) -> None:
    uri = f"image://{helper.cluster_name}/{helper.username}/{uuid4()}:latest"
    another_test_user = "test2"
    with pytest.raises(subprocess.CalledProcessError) as cm:
        request.addfinalizer(lambda: revoke(helper, uri, another_test_user))
        helper.run_cli(["acl", "grant", uri, another_test_user, "read"])
    assert cm.value.returncode == 127
    assert "tag is not allowed" in cm.value.stderr


@pytest.mark.e2e
def test_list_role(request: Any, helper: Helper) -> None:
    captured = helper.run_cli(["acl", "list", "-s", "role"])
    assert captured.err == ""
    result = captured.out.splitlines()
    self_role_uri = f"role://{helper.username}"
    role = helper.username
    for line in result:
        uri, *_ = line.split()
        assert uri.startswith("role://")
        if uri != self_role_uri:
            role = uri[len("role://") :]
    print(f"Test using role {role!r}")

    captured = helper.run_cli(["acl", "list", "-u", role])
    assert captured.err == ""

    captured = helper.run_cli(["acl", "list", "-u", role, "--shared"])
    assert captured.err == ""


@pytest.mark.e2e
def test_list_role_forbidden(request: Any, helper: Helper) -> None:
    with pytest.raises(subprocess.CalledProcessError):
        helper.run_cli(["acl", "list", "-u", "admin"])
    with pytest.raises(subprocess.CalledProcessError):
        helper.run_cli(["acl", "list", "-u", "admin", "--shared"])
