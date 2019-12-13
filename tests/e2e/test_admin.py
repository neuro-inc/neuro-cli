import pytest

from tests.e2e.conftest import Helper


@pytest.mark.e2e
def test_list_clusters(helper: Helper) -> None:
    # should not fail
    helper.run_cli(["admin", "get-clusters"])


@pytest.mark.e2e
def test_list_cluster_users(helper: Helper) -> None:
    # should not fail
    helper.run_cli(["admin", "get-cluster-users"])
