from typing import Callable, List
from unittest import mock

from neuromation.api.admin import _Admin, _ClusterUser, _ClusterUserRoleType

from .conftest import SysCapWithCode


_RunCli = Callable[[List[str]], SysCapWithCode]


def test_add_cluster_user_print_result(run_cli: _RunCli) -> None:
    with mock.patch.object(_Admin, "add_cluster_user") as mocked:

        async def add_cluster_user(
            cluster_name: str, user_name: str, role: str
        ) -> _ClusterUser:
            # NOTE: We return a different role to check that we print it to user
            return _ClusterUser(user_name, _ClusterUserRoleType.MANAGER)

        mocked.side_effect = add_cluster_user
        capture = run_cli(["admin", "add-cluster-user", "default", "ivan", "admin"])
        assert not capture.err
        assert capture.out == "Added ivan to cluster default as manager"

        # Same with quiet mode
        mocked.side_effect = add_cluster_user
        capture = run_cli(
            ["-q", "admin", "add-cluster-user", "default", "ivan", "admin"]
        )
        assert not capture.err
        assert not capture.out


def test_remove_cluster_user_print_result(run_cli: _RunCli) -> None:
    with mock.patch.object(_Admin, "remove_cluster_user") as mocked:

        async def remove_cluster_user(cluster_name: str, user_name: str) -> None:
            return

        mocked.side_effect = remove_cluster_user
        capture = run_cli(["admin", "remove-cluster-user", "default", "ivan"])
        assert not capture.err
        assert capture.out == "Removed ivan from cluster default"

        # Same with quiet mode
        mocked.side_effect = remove_cluster_user
        capture = run_cli(["-q", "admin", "remove-cluster-user", "default", "ivan"])
        assert not capture.err
        assert not capture.out
