import secrets
import subprocess
from pathlib import Path
from typing import Iterator, List, Tuple

import pytest

from tests.e2e import Helper

pytestmark = pytest.mark.require_admin


@pytest.fixture
def tmp_test_cluster(helper: Helper, tmp_path: Path) -> Iterator[str]:
    cluster_name = "e2e-testing-" + secrets.token_hex(10)
    fake_conf = tmp_path / "fake_cluster_config"
    fake_conf.write_text("")
    helper.run_cli(
        ["admin", "add-cluster", "--skip-provisioning", cluster_name, str(fake_conf)]
    )
    try:
        yield cluster_name
    finally:
        helper.run_cli(["admin", "remove-cluster", "--force", cluster_name])


@pytest.mark.e2e
def test_list_clusters(helper: Helper, tmp_test_cluster: str) -> None:
    captured = helper.run_cli(["admin", "get-clusters"])
    assert tmp_test_cluster in captured.out


@pytest.mark.e2e
def test_list_cluster_users_admin_only(helper: Helper, tmp_test_cluster: str) -> None:
    captured = helper.run_cli(["admin", "get-cluster-users", tmp_test_cluster])
    user_line = captured.out.split("\n")[3]
    assert helper.username in user_line
    assert "admin" in user_line


@pytest.mark.e2e
def test_list_cluster_users_added_members(
    helper: Helper, tmp_test_cluster: str, test_user_names: List[str]
) -> None:
    name_to_role = {
        test_user_names[0]: "user",
        test_user_names[1]: "user",
        test_user_names[2]: "manager",
        test_user_names[3]: "admin",
    }
    for name, role in name_to_role.items():
        helper.run_cli(["admin", "add-cluster-user", tmp_test_cluster, name, role])
    captured = helper.run_cli(["admin", "get-cluster-users", tmp_test_cluster])
    user_lines = captured.out.split("\n")[3:]
    for name, role in name_to_role.items():
        assert any(name in line and role in line for line in user_lines)


@pytest.mark.e2e
def test_add_cluster_user_already_exists(
    helper: Helper, tmp_test_cluster: str, test_user_names: List[str]
) -> None:
    test_user = test_user_names[0]
    helper.run_cli(["admin", "add-cluster-user", tmp_test_cluster, test_user, "user"])
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(
            ["admin", "add-cluster-user", tmp_test_cluster, test_user, "user"]
        )
    assert cm.value.returncode == 65
    assert (
        f"Illegal argument(s) (User '{test_user}' already exists in cluster "
        f"'{tmp_test_cluster}')" in cm.value.stderr
    )


@pytest.mark.e2e
def test_add_cluster_user_does_not_exist(
    helper: Helper,
    tmp_test_cluster: str,
) -> None:
    username = "some-clearly-invalid-username"
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(
            ["admin", "add-cluster-user", tmp_test_cluster, username, "user"]
        )
    assert cm.value.returncode == 72
    assert f"User 'some-clearly-invalid-username' not found" in cm.value.stderr


@pytest.mark.e2e
def test_add_cluster_user_invalid_role(
    helper: Helper, tmp_test_cluster: str, test_user_names: List[str]
) -> None:
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(
            [
                "admin",
                "add-cluster-user",
                tmp_test_cluster,
                test_user_names[0],
                "my_role",
            ]
        )
    assert cm.value.returncode == 2
    assert "Invalid value for '[ROLE]'" in cm.value.stderr


@pytest.mark.e2e
def test_remove_cluster_user_remove_oneself(
    helper: Helper, tmp_test_cluster: str
) -> None:
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(
            ["admin", "remove-cluster-user", tmp_test_cluster, helper.username]
        )
    assert cm.value.returncode == 65
    assert (
        "Illegal argument(s) (Cluster users cannot remove themselves)"
        in cm.value.stderr
    )


@pytest.mark.e2e
def test_remove_cluster_user_does_not_exist(
    helper: Helper, tmp_test_cluster: str
) -> None:
    username = "some-clearly-invalid-username"
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(["admin", "remove-cluster-user", tmp_test_cluster, username])
    assert cm.value.returncode == 72
    assert f"User 'some-clearly-invalid-username' not found" in cm.value.stderr


@pytest.mark.e2e
def test_cluster_user_default_unlimited_quota(
    helper: Helper, tmp_test_cluster: str, test_user_names: List[str]
) -> None:
    username = test_user_names[0]
    helper.run_cli(["admin", "add-cluster-user", tmp_test_cluster, username, "user"])
    captured = helper.run_cli(["admin", "get-user-quota", tmp_test_cluster, username])
    assert "Jobs: infinity" in captured.out
    assert "Credits: infinity" in captured.out


@pytest.mark.e2e
def test_cluster_user_set_quota_during_add(
    helper: Helper, tmp_test_cluster: str, test_user_names: List[str]
) -> None:
    username = test_user_names[0]
    helper.run_cli(
        [
            "admin",
            "add-cluster-user",
            "-c",
            "200.22",
            "-j",
            "20",
            tmp_test_cluster,
            username,
            "user",
        ]
    )
    captured = helper.run_cli(["admin", "get-user-quota", tmp_test_cluster, username])
    assert "Jobs: 20" in captured.out
    assert "Credits: 200.22" in captured.out


@pytest.mark.e2e
def test_cluster_user_default_set_balance_and_quota(
    helper: Helper, tmp_test_cluster: str, test_user_names: List[str]
) -> None:
    username = test_user_names[0]
    helper.run_cli(["admin", "add-cluster-user", tmp_test_cluster, username, "user"])
    helper.run_cli(
        ["admin", "set-user-credits", "-c", "200.22", tmp_test_cluster, username]
    )
    helper.run_cli(["admin", "set-user-quota", "-j", "20", tmp_test_cluster, username])
    captured = helper.run_cli(["admin", "get-user-quota", tmp_test_cluster, username])
    assert "Jobs: 20" in captured.out
    assert "Credits: 200.22" in captured.out


@pytest.mark.e2e
def test_cluster_user_default_set_balance_and_quota_to_unlimited(
    helper: Helper, tmp_test_cluster: str, test_user_names: List[str]
) -> None:
    username = test_user_names[0]
    helper.run_cli(
        [
            "admin",
            "add-cluster-user",
            "-c",
            "200.22",
            "-j",
            "20",
            tmp_test_cluster,
            username,
            "user",
        ]
    )
    helper.run_cli(["admin", "set-user-credits", tmp_test_cluster, username])
    helper.run_cli(["admin", "set-user-quota", tmp_test_cluster, username])
    captured = helper.run_cli(["admin", "get-user-quota", tmp_test_cluster, username])
    assert "Jobs: infinity" in captured.out
    assert "Credits: infinity" in captured.out


@pytest.fixture
def tmp_test_org(helper: Helper) -> Iterator[str]:
    org_name = "e2e-testing-" + secrets.token_hex(10)
    helper.run_cli(["admin", "add-org", org_name])
    try:
        yield org_name
    finally:
        helper.run_cli(["admin", "remove-org", "--force", org_name])


@pytest.mark.e2e
def test_list_orgs(helper: Helper, tmp_test_org: str) -> None:
    captured = helper.run_cli(["admin", "get-orgs"])
    assert tmp_test_org in captured.out


@pytest.mark.e2e
def test_list_org_users_admin_only(helper: Helper, tmp_test_org: str) -> None:
    captured = helper.run_cli(["admin", "get-org-users", tmp_test_org])
    user_line = captured.out.split("\n")[3]
    assert helper.username in user_line
    assert "admin" in user_line


@pytest.mark.e2e
def test_list_org_users_added_members(
    helper: Helper, tmp_test_org: str, test_user_names: List[str]
) -> None:
    name_to_role = {
        test_user_names[0]: "user",
        test_user_names[1]: "user",
        test_user_names[2]: "manager",
        test_user_names[3]: "admin",
    }
    for name, role in name_to_role.items():
        helper.run_cli(["admin", "add-org-user", tmp_test_org, name, role])
    captured = helper.run_cli(["admin", "get-org-users", tmp_test_org])
    user_lines = captured.out.split("\n")[3:]
    for name, role in name_to_role.items():
        assert any(name in line and role in line for line in user_lines)


@pytest.mark.e2e
def test_add_org_user_already_exists(
    helper: Helper, tmp_test_org: str, test_user_names: List[str]
) -> None:
    test_user = test_user_names[0]
    helper.run_cli(["admin", "add-org-user", tmp_test_org, test_user, "user"])
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(["admin", "add-org-user", tmp_test_org, test_user, "user"])
    assert cm.value.returncode == 65
    assert (
        f"Illegal argument(s) (User '{test_user}' already exists in org "
        f"'{tmp_test_org}')" in cm.value.stderr
    )


@pytest.mark.e2e
def test_add_org_user_does_not_exist(
    helper: Helper,
    tmp_test_org: str,
) -> None:
    username = "some-clearly-invalid-username"
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(["admin", "add-org-user", tmp_test_org, username, "user"])
    assert cm.value.returncode == 72
    assert f"User 'some-clearly-invalid-username' not found" in cm.value.stderr


@pytest.mark.e2e
def test_add_org_user_invalid_role(
    helper: Helper, tmp_test_org: str, test_user_names: List[str]
) -> None:
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(
            [
                "admin",
                "add-org-user",
                tmp_test_org,
                test_user_names[0],
                "my_role",
            ]
        )
    assert cm.value.returncode == 2
    assert "Invalid value for '[ROLE]'" in cm.value.stderr


@pytest.mark.e2e
def test_remove_org_user_remove_oneself(helper: Helper, tmp_test_org: str) -> None:
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(["admin", "remove-org-user", tmp_test_org, helper.username])
    assert cm.value.returncode == 65
    assert "Illegal argument(s) (Org users cannot remove themselves)" in cm.value.stderr


@pytest.mark.e2e
def test_remove_org_user_does_not_exist(helper: Helper, tmp_test_org: str) -> None:
    username = "some-clearly-invalid-username"
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(["admin", "remove-org-user", tmp_test_org, username])
    assert cm.value.returncode == 72
    assert f"User 'some-clearly-invalid-username' not found" in cm.value.stderr


@pytest.mark.e2e
def test_list_org_clusters(
    helper: Helper, tmp_test_org: str, tmp_test_cluster: str
) -> None:
    helper.run_cli(["admin", "add-org-cluster", tmp_test_cluster, tmp_test_org])
    captured = helper.run_cli(["admin", "get-org-clusters", tmp_test_cluster])
    org_cluster_lines = captured.out.split("\n")[3:]
    assert any(
        tmp_test_org in line and tmp_test_cluster in line for line in org_cluster_lines
    )


@pytest.mark.e2e
def test_remove_org_cluster(
    helper: Helper, tmp_test_org: str, tmp_test_cluster: str
) -> None:
    helper.run_cli(["admin", "add-org-cluster", tmp_test_cluster, tmp_test_org])
    helper.run_cli(
        ["admin", "remove-org-cluster", "--force", tmp_test_cluster, tmp_test_org]
    )
    captured = helper.run_cli(["admin", "get-org-clusters", tmp_test_cluster])
    assert tmp_test_org not in captured.out


@pytest.fixture
def tmp_test_org_cluster(
    helper: Helper, tmp_test_cluster: str, tmp_test_org: str
) -> Iterator[Tuple[str, str]]:
    helper.run_cli(["admin", "add-org-cluster", tmp_test_cluster, tmp_test_org])
    try:
        yield tmp_test_cluster, tmp_test_org
    finally:
        helper.run_cli(
            ["admin", "remove-org-cluster", "--force", tmp_test_cluster, tmp_test_org]
        )


@pytest.mark.e2e
def test_list_org_cluster_users_added_members(
    helper: Helper, tmp_test_org_cluster: Tuple[str, str], test_user_names: List[str]
) -> None:
    name_to_role = {
        test_user_names[0]: "user",
        test_user_names[1]: "user",
        test_user_names[2]: "manager",
        test_user_names[3]: "admin",
    }
    cluster_name, org_name = tmp_test_org_cluster
    for name, role in name_to_role.items():
        helper.run_cli(["admin", "add-org-user", org_name, name])
        helper.run_cli(
            ["admin", "add-cluster-user", "--org", org_name, cluster_name, name, role]
        )
    captured = helper.run_cli(
        ["admin", "get-cluster-users", "--org", org_name, cluster_name]
    )
    user_lines = captured.out.split("\n")[3:]
    for name, role in name_to_role.items():
        assert any(name in line and role in line for line in user_lines)


@pytest.mark.e2e
def test_remove_org_cluster_user_remove_oneself(
    helper: Helper,
    tmp_test_org_cluster: Tuple[str, str],
) -> None:
    cluster_name, org_name = tmp_test_org_cluster
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(
            [
                "admin",
                "remove-cluster-user",
                "--org",
                org_name,
                cluster_name,
                helper.username,
            ]
        )
    assert cm.value.returncode == 65
    assert (
        "Illegal argument(s) (Cluster users cannot remove themselves)"
        in cm.value.stderr
    )


@pytest.mark.e2e
def test_add_org_cluster_user_non_org_user_fails(
    helper: Helper, tmp_test_org_cluster: Tuple[str, str], test_user_names: List[str]
) -> None:
    cluster_name, org_name = tmp_test_org_cluster
    username = test_user_names[0]
    with pytest.raises(subprocess.CalledProcessError) as cm:
        helper.run_cli(
            [
                "admin",
                "add-cluster-user",
                "--org",
                org_name,
                cluster_name,
                username,
                "user",
            ]
        )
    assert cm.value.returncode == 72
    assert f"User '{username}' not found in org '{org_name}'" in cm.value.stderr


@pytest.mark.e2e
def test_org_cluster_user_default_unlimited_quota(
    helper: Helper, tmp_test_org_cluster: Tuple[str, str], test_user_names: List[str]
) -> None:
    cluster_name, org_name = tmp_test_org_cluster
    username = test_user_names[0]
    helper.run_cli(["admin", "add-org-user", org_name, username])
    helper.run_cli(
        ["admin", "add-cluster-user", "--org", org_name, cluster_name, username, "user"]
    )
    captured = helper.run_cli(
        ["admin", "get-user-quota", "--org", org_name, cluster_name, username]
    )
    assert "Jobs: infinity" in captured.out
    assert "Credits: infinity" in captured.out


@pytest.mark.e2e
def test_org_cluster_user_set_quota_during_add(
    helper: Helper, tmp_test_org_cluster: Tuple[str, str], test_user_names: List[str]
) -> None:
    cluster_name, org_name = tmp_test_org_cluster
    username = test_user_names[0]
    helper.run_cli(["admin", "add-org-user", org_name, username])
    helper.run_cli(
        [
            "admin",
            "add-cluster-user",
            "-c",
            "200.22",
            "-j",
            "20",
            "--org",
            org_name,
            cluster_name,
            username,
            "user",
        ]
    )
    captured = helper.run_cli(
        ["admin", "get-user-quota", "--org", org_name, cluster_name, username]
    )
    assert "Jobs: 20" in captured.out
    assert "Credits: 200.22" in captured.out


@pytest.mark.e2e
def test_org_cluster_user_default_set_balance_and_quota(
    helper: Helper, tmp_test_org_cluster: Tuple[str, str], test_user_names: List[str]
) -> None:
    cluster_name, org_name = tmp_test_org_cluster
    username = test_user_names[0]
    helper.run_cli(["admin", "add-org-user", org_name, username])
    helper.run_cli(
        ["admin", "add-cluster-user", "--org", org_name, cluster_name, username, "user"]
    )
    helper.run_cli(
        [
            "admin",
            "set-user-credits",
            "-c",
            "200.22",
            "--org",
            org_name,
            cluster_name,
            username,
        ]
    )
    helper.run_cli(
        [
            "admin",
            "set-user-quota",
            "-j",
            "20",
            "--org",
            org_name,
            cluster_name,
            username,
        ]
    )
    captured = helper.run_cli(
        ["admin", "get-user-quota", "--org", org_name, cluster_name, username]
    )
    assert "Jobs: 20" in captured.out
    assert "Credits: 200.22" in captured.out


@pytest.mark.e2e
def test_org_cluster_default_unlimited_quota(
    helper: Helper,
    tmp_test_cluster: str,
    tmp_test_org: str,
) -> None:
    helper.run_cli(["admin", "add-org-cluster", tmp_test_cluster, tmp_test_org])
    captured = helper.run_cli(
        ["admin", "get-org-cluster-quota", tmp_test_cluster, tmp_test_org]
    )
    assert "Jobs: infinity" in captured.out
    assert "Credits: infinity" in captured.out


@pytest.mark.e2e
def test_org_cluster_set_quota_during_add(
    helper: Helper,
    tmp_test_cluster: str,
    tmp_test_org: str,
) -> None:
    helper.run_cli(
        [
            "admin",
            "add-org-cluster",
            "-c",
            "200.22",
            "-j",
            "20",
            tmp_test_cluster,
            tmp_test_org,
        ]
    )
    captured = helper.run_cli(
        ["admin", "get-org-cluster-quota", tmp_test_cluster, tmp_test_org]
    )
    assert "Jobs: 20" in captured.out
    assert "Credits: 200.22" in captured.out


@pytest.mark.e2e
def test_org_cluster_set_balance_and_quota(
    helper: Helper,
    tmp_test_cluster: str,
    tmp_test_org: str,
) -> None:
    helper.run_cli(["admin", "add-org-cluster", tmp_test_cluster, tmp_test_org])
    helper.run_cli(
        [
            "admin",
            "set-org-cluster-credits",
            "-c",
            "200.22",
            tmp_test_cluster,
            tmp_test_org,
        ]
    )
    helper.run_cli(
        ["admin", "set-org-cluster-quota", "-j", "20", tmp_test_cluster, tmp_test_org]
    )
    captured = helper.run_cli(
        ["admin", "get-org-cluster-quota", tmp_test_cluster, tmp_test_org]
    )
    assert "Jobs: 20" in captured.out
    assert "Credits: 200.22" in captured.out


@pytest.mark.e2e
def test_org_cluster_set_balance_and_quota_to_unlimited(
    helper: Helper,
    tmp_test_cluster: str,
    tmp_test_org: str,
) -> None:
    helper.run_cli(
        [
            "admin",
            "add-org-cluster",
            "-c",
            "200.22",
            "-j",
            "20",
            tmp_test_cluster,
            tmp_test_org,
        ]
    )
    helper.run_cli(["admin", "set-org-cluster-credits", tmp_test_cluster, tmp_test_org])
    helper.run_cli(["admin", "set-org-cluster-quota", tmp_test_cluster, tmp_test_org])
    captured = helper.run_cli(
        ["admin", "get-org-cluster-quota", tmp_test_cluster, tmp_test_org]
    )
    assert "Jobs: infinity" in captured.out
    assert "Credits: infinity" in captured.out
