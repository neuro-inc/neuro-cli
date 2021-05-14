import subprocess

import pytest

from tests.e2e import Helper

pytestmark = pytest.mark.require_admin


@pytest.mark.e2e
def test_list_clusters(helper: Helper) -> None:
    # should not fail
    helper.run_cli(["admin", "get-clusters"])


@pytest.mark.e2e
def test_list_cluster_users(helper: Helper) -> None:
    # should not fail
    helper.run_cli(["admin", "get-cluster-users"])


@pytest.mark.e2e
@pytest.mark.require_admin
def test_get_cluster_users(helper: Helper) -> None:
    captured = helper.run_cli(["admin", "get-cluster-users"])
    assert captured.err == ""

    for role in ["admin", "manager", "user"]:
        assert role in captured.out


@pytest.mark.e2e
def test_add_cluster_user_already_exists(helper: Helper) -> None:
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(
            ["admin", "add-cluster-user", helper.cluster_name, helper.username, "user"]
        )
    assert cm.value.returncode == 65
    assert (
        f"Illegal argument(s) (User '{helper.username}' already exists in cluster "
        f"'{helper.cluster_name}')" in cm.value.stderr
    )


@pytest.mark.e2e
def test_add_cluster_user_does_not_exist(helper: Helper) -> None:
    username = "some-clearly-invalid-username"
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(
            ["admin", "add-cluster-user", helper.cluster_name, username, "user"]
        )
    assert cm.value.returncode == 72
    assert f"User 'some-clearly-invalid-username' not found" in cm.value.stderr


@pytest.mark.e2e
def test_add_cluster_user_invalid_role(helper: Helper) -> None:
    username = "some-clearly-invalid-username"
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(
            ["admin", "add-cluster-user", helper.cluster_name, username, "my_role"]
        )
    assert cm.value.returncode == 2
    assert "Invalid value for '[ROLE]'" in cm.value.stderr


@pytest.mark.e2e
def test_remove_cluster_user_remove_oneself(helper: Helper) -> None:
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(
            ["admin", "remove-cluster-user", helper.cluster_name, helper.username]
        )
    assert cm.value.returncode == 65
    assert (
        "Illegal argument(s) (Cluster users cannot remove themselves)"
        in cm.value.stderr
    )


@pytest.mark.e2e
def test_remove_cluster_user_does_not_exist(helper: Helper) -> None:
    username = "some-clearly-invalid-username"
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(["admin", "remove-cluster-user", helper.cluster_name, username])
    assert cm.value.returncode == 72
    assert f"User 'some-clearly-invalid-username' not found" in cm.value.stderr
