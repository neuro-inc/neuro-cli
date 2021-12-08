import json
from contextlib import ExitStack, contextmanager
from decimal import Decimal
from typing import Any, Callable, Iterator, List, Mapping, Optional
from unittest import mock

from neuro_sdk import (
    Preset,
    _Admin,
    _Balance,
    _ClusterUserRoleType,
    _ClusterUserWithInfo,
    _Quota,
    _UserInfo,
)
from neuro_sdk._config import Config

from .conftest import SysCapWithCode

_RunCli = Callable[[List[str]], SysCapWithCode]


@contextmanager
def mock_create_cluster_user() -> Iterator[None]:
    with mock.patch.object(_Admin, "create_cluster_user") as mocked:

        async def create_cluster_user(
            cluster_name: str,
            user_name: str,
            role: _ClusterUserRoleType,
            balance: _Balance,
            quota: _Quota,
            org_name: Optional[str] = None,
        ) -> _ClusterUserWithInfo:
            # NOTE: We return a different role to check that we print it to user
            return _ClusterUserWithInfo(
                user_name=user_name,
                cluster_name=cluster_name,
                org_name=org_name,
                role=_ClusterUserRoleType.MANAGER,
                quota=quota,
                balance=balance,
                user_info=_UserInfo(
                    email="some@email.com",
                    created_at=None,
                    first_name=None,
                    last_name=None,
                ),
            )

        mocked.side_effect = create_cluster_user
        yield


def test_add_cluster_user_print_result(run_cli: _RunCli) -> None:
    with mock_create_cluster_user():
        capture = run_cli(["admin", "add-cluster-user", "default", "ivan", "admin"])
    assert not capture.err
    assert capture.out == "Added ivan to cluster default as manager"
    assert capture.code == 0

    # Same with quiet mode
    with mock_create_cluster_user():
        capture = run_cli(
            ["-q", "admin", "add-cluster-user", "default", "ivan", "admin"]
        )
    assert not capture.err
    assert not capture.out
    assert capture.code == 0


def test_add_cluster_user_with_credits(run_cli: _RunCli) -> None:
    for value in ("1234.5", "0", "-1234.5", "unlimited"):
        with mock_create_cluster_user():
            capture = run_cli(
                [
                    "admin",
                    "add-cluster-user",
                    "default",
                    "ivan",
                    "admin",
                    "--credits",
                    value,
                ]
            )
        assert not capture.err
        assert capture.code == 0

    for value in ("spam", "inf", "nan", "infinity", "Infinity"):
        with mock_create_cluster_user():
            capture = run_cli(
                [
                    "admin",
                    "add-cluster-user",
                    "default",
                    "ivan",
                    "admin",
                    "--credits",
                    value,
                ]
            )
        assert f"{value} is not valid decimal number" in capture.err, capture
        assert capture.code == 2


def test_add_cluster_user_with_jobs(run_cli: _RunCli) -> None:
    for value in ("100", "0", "unlimited"):
        with mock_create_cluster_user():
            capture = run_cli(
                [
                    "admin",
                    "add-cluster-user",
                    "default",
                    "ivan",
                    "admin",
                    "--jobs",
                    value,
                ]
            )
        assert not capture.err
        assert capture.code == 0

    for value in ("spam", "-100", "10.5", "inf", "nan", "infinity", "Infinity"):
        with mock_create_cluster_user():
            capture = run_cli(
                [
                    "admin",
                    "add-cluster-user",
                    "default",
                    "ivan",
                    "admin",
                    "--jobs",
                    value,
                ]
            )
        assert f"jobs quota should be non-negative integer" in capture.err, capture
        assert capture.code == 2


def test_set_user_credits(run_cli: _RunCli) -> None:
    with mock.patch.object(_Admin, "update_cluster_user_balance") as mocked:

        async def update_cluster_user_balance(
            cluster_name: str,
            user_name: str,
            credits: Optional[Decimal],
            org_name: Optional[str] = None,
        ) -> _ClusterUserWithInfo:
            return _ClusterUserWithInfo(
                cluster_name=cluster_name,
                user_name=user_name,
                role=_ClusterUserRoleType.USER,
                quota=_Quota(),
                balance=_Balance(credits=credits),
                org_name=org_name,
                user_info=_UserInfo(email=f"{user_name}@example.org"),
            )

        for value, outvalue in (
            ("1234.5", "1234.50"),
            ("0", "0.00"),
            ("-1234.5", "-1234.50"),
            ("unlimited", "unlimited"),
        ):
            mocked.side_effect = update_cluster_user_balance
            capture = run_cli(
                ["admin", "set-user-credits", "default", "ivan", "--credits", value]
            )
            assert not capture.err
            assert capture.out == (
                f"New credits for ivan on cluster default:\n"
                f"Credits: {outvalue}\n"
                f"Spend credits: 0.00"
            )
            assert capture.code == 0

        for value in ("spam", "inf", "nan", "infinity", "Infinity"):
            mocked.side_effect = update_cluster_user_balance
            capture = run_cli(
                ["admin", "set-user-credits", "default", "ivan", "--credits", value]
            )
            assert f"{value} is not valid decimal number" in capture.err
            assert capture.code == 2

        mocked.side_effect = update_cluster_user_balance
        capture = run_cli(["admin", "set-user-credits", "default", "ivan"])
        assert "Missing option '-c' / '--credits'." in capture.err
        assert capture.code == 2


def test_add_user_credits(run_cli: _RunCli) -> None:
    with mock.patch.object(_Admin, "update_cluster_user_balance_by_delta") as mocked:

        async def update_cluster_user_balance_by_delta(
            cluster_name: str,
            user_name: str,
            delta: Decimal,
            org_name: Optional[str] = None,
        ) -> _ClusterUserWithInfo:
            return _ClusterUserWithInfo(
                cluster_name=cluster_name,
                user_name=user_name,
                role=_ClusterUserRoleType.USER,
                quota=_Quota(),
                balance=_Balance(credits=100 + delta),
                org_name=org_name,
                user_info=_UserInfo(email=f"{user_name}@example.org"),
            )

        for value, outvalue in (
            ("1234.5", "1334.50"),
            ("0", "100.00"),
            ("-1234.5", "-1134.50"),
        ):
            mocked.side_effect = update_cluster_user_balance_by_delta
            capture = run_cli(
                ["admin", "add-user-credits", "default", "ivan", "--credits", value]
            )
            assert not capture.err
            assert capture.out == (
                f"New credits for ivan on cluster default:\n"
                f"Credits: {outvalue}\n"
                f"Spend credits: 0.00"
            )
            assert capture.code == 0

        for value in ("spam", "unlimited", "inf", "nan", "infinity", "Infinity"):
            mocked.side_effect = update_cluster_user_balance_by_delta
            capture = run_cli(
                ["admin", "add-user-credits", "default", "ivan", "--credits", value]
            )
            assert f"{value} is not valid decimal number" in capture.err
            assert capture.code == 2

        mocked.side_effect = update_cluster_user_balance_by_delta
        capture = run_cli(["admin", "add-user-credits", "default", "ivan"])
        assert "Missing option '-c' / '--credits'." in capture.err
        assert capture.code == 2


def test_set_user_quota(run_cli: _RunCli) -> None:
    with mock.patch.object(_Admin, "update_cluster_user_quota") as mocked:

        async def update_cluster_user_quota(
            cluster_name: str,
            user_name: str,
            quota: _Quota,
            org_name: Optional[str] = None,
        ) -> _ClusterUserWithInfo:
            return _ClusterUserWithInfo(
                cluster_name=cluster_name,
                user_name=user_name,
                role=_ClusterUserRoleType.USER,
                quota=quota,
                balance=_Balance(),
                org_name=org_name,
                user_info=_UserInfo(email=f"{user_name}@example.org"),
            )

        for value in ("100", "0", "unlimited"):
            mocked.side_effect = update_cluster_user_quota
            capture = run_cli(
                ["admin", "set-user-quota", "default", "ivan", "--jobs", value]
            )
            assert not capture.err
            assert (
                capture.out == f"New quotas for ivan on cluster default:\nJobs: {value}"
            )
            assert capture.code == 0

        for value in ("spam", "-100", "10.5", "inf", "nan", "infinity", "Infinity"):
            mocked.side_effect = update_cluster_user_quota
            capture = run_cli(
                ["admin", "set-user-quota", "default", "ivan", "--jobs", value]
            )
            assert "jobs quota should be non-negative integer" in capture.err
            assert capture.code == 2

        mocked.side_effect = update_cluster_user_quota
        capture = run_cli(["admin", "set-user-quota", "default", "ivan"])
        assert "Missing option '-j' / '--jobs'." in capture.err
        assert capture.code == 2


def test_remove_cluster_user_print_result(run_cli: _RunCli) -> None:
    with mock.patch.object(_Admin, "delete_cluster_user") as mocked:

        async def delete_cluster_user(
            cluster_name: str,
            user_name: str,
            org_name: Optional[str] = None,
        ) -> None:
            return

        mocked.side_effect = delete_cluster_user
        capture = run_cli(["admin", "remove-cluster-user", "default", "ivan"])
        assert not capture.err
        assert capture.out == "Removed ivan from cluster default"

        # Same with quiet mode
        mocked.side_effect = delete_cluster_user
        capture = run_cli(["-q", "admin", "remove-cluster-user", "default", "ivan"])
        assert not capture.err
        assert not capture.out


def test_show_cluster_config_options(run_cli: _RunCli) -> None:
    with mock.patch.object(_Admin, "get_cloud_provider_options") as mocked:
        sample_data = {"foo": "bar", "baz": {"t2": 1, "t1": 2}}

        async def get_cloud_provider_options(
            cloud_provider_name: str,
        ) -> Mapping[str, Any]:
            assert cloud_provider_name == "aws"
            return sample_data

        mocked.side_effect = get_cloud_provider_options
        capture = run_cli(["admin", "show-cluster-options", "--type", "aws"])
        assert not capture.err

        assert json.loads(capture.out) == sample_data


def test_add_resource_preset(run_cli: _RunCli) -> None:
    with ExitStack() as exit_stack:
        admin_mocked = exit_stack.enter_context(
            mock.patch.object(_Admin, "update_cluster_resource_presets")
        )
        config_mocked = exit_stack.enter_context(mock.patch.object(Config, "fetch"))

        async def update_cluster_resource_presets(
            cluster_name: str, presets: Mapping[str, Preset]
        ) -> None:
            assert cluster_name == "default"
            assert "cpu-micro" in presets
            assert presets["cpu-micro"] == Preset(
                credits_per_hour=Decimal("10"),
                cpu=0.1,
                memory_mb=100,
                gpu=1,
                gpu_model="nvidia-tesla-k80",
                tpu_type="v2-8",
                tpu_software_version="1.14",
                scheduler_enabled=True,
                preemptible_node=True,
            )
            exit_stack.enter_context(
                mock.patch.object(Config, "presets", dict(presets))
            )

        async def fetch() -> None:
            pass

        admin_mocked.side_effect = update_cluster_resource_presets
        config_mocked.side_effect = fetch

        capture = run_cli(
            [
                "admin",
                "add-resource-preset",
                "cpu-micro",
                "--credits-per-hour",
                "10.00",
                "-c",
                "0.1",
                "-m",
                "100M",
                "-g",
                "1",
                "--gpu-model",
                "nvidia-tesla-k80",
                "--tpu-type",
                "v2-8",
                "--tpu-sw-version",
                "1.14",
                "-p",
                "--preemptible-node",
            ]
        )
        assert capture.code == 0, capture.out + capture.err


def test_add_existing_resource_preset_not_allowed(run_cli: _RunCli) -> None:
    with ExitStack() as exit_stack:
        admin_mocked = exit_stack.enter_context(
            mock.patch.object(_Admin, "update_cluster_resource_presets")
        )
        config_mocked = exit_stack.enter_context(mock.patch.object(Config, "fetch"))

        async def update_cluster_resource_presets(
            cluster_name: str, presets: Mapping[str, Preset]
        ) -> None:
            pass

        async def fetch() -> None:
            pass

        admin_mocked.side_effect = update_cluster_resource_presets
        config_mocked.side_effect = fetch

        capture = run_cli(
            [
                "admin",
                "add-resource-preset",
                "cpu-small",
            ]
        )
        assert capture.code == 127, capture.out + capture.err
        assert "Preset 'cpu-small' already exists" in capture.err


def test_update_resource_preset(run_cli: _RunCli) -> None:
    with ExitStack() as exit_stack:
        admin_mocked = exit_stack.enter_context(
            mock.patch.object(_Admin, "update_cluster_resource_presets")
        )
        config_mocked = exit_stack.enter_context(mock.patch.object(Config, "fetch"))

        async def update_cluster_resource_presets(
            cluster_name: str, presets: Mapping[str, Preset]
        ) -> None:
            assert cluster_name == "default"
            assert "cpu-small" in presets
            assert presets["cpu-small"] == Preset(
                credits_per_hour=Decimal("122"), cpu=7, memory_mb=2 * 1024
            )
            exit_stack.enter_context(
                mock.patch.object(Config, "presets", dict(presets))
            )

        async def fetch() -> None:
            pass

        admin_mocked.side_effect = update_cluster_resource_presets
        config_mocked.side_effect = fetch

        capture = run_cli(
            [
                "admin",
                "update-resource-preset",
                "cpu-small",
                "--credits-per-hour",
                "122.00",
            ]
        )
        assert capture.code == 0, capture.out + capture.err


def test_add_resource_preset_print_result(run_cli: _RunCli) -> None:
    with ExitStack() as exit_stack:
        admin_mocked = exit_stack.enter_context(
            mock.patch.object(_Admin, "update_cluster_resource_presets")
        )
        config_mocked = exit_stack.enter_context(mock.patch.object(Config, "fetch"))

        async def update_cluster_resource_presets(
            cluster_name: str, presets: Mapping[str, Preset]
        ) -> None:
            exit_stack.enter_context(
                mock.patch.object(Config, "presets", dict(presets))
            )

        async def fetch() -> None:
            pass

        admin_mocked.side_effect = update_cluster_resource_presets
        config_mocked.side_effect = fetch

        capture = run_cli(["admin", "add-resource-preset", "cpu-micro"])
        assert not capture.err
        assert capture.out == "Added resource preset cpu-micro in cluster default"

        # Same with quiet mode
        capture = run_cli(["-q", "admin", "add-resource-preset", "cpu-micro-2"])
        assert not capture.err
        assert not capture.out


def test_remove_resource_preset_print_result(run_cli: _RunCli) -> None:
    with ExitStack() as exit_stack:
        admin_mocked = exit_stack.enter_context(
            mock.patch.object(_Admin, "update_cluster_resource_presets")
        )
        config_mocked = exit_stack.enter_context(mock.patch.object(Config, "fetch"))

        async def update_cluster_resource_presets(
            cluster_name: str, presets: Mapping[str, Preset]
        ) -> None:
            exit_stack.enter_context(
                mock.patch.object(Config, "presets", dict(presets))
            )

        async def fetch() -> None:
            pass

        admin_mocked.side_effect = update_cluster_resource_presets
        config_mocked.side_effect = fetch

        capture = run_cli(["admin", "remove-resource-preset", "cpu-small"])
        assert not capture.err
        assert capture.out == "Removed resource preset cpu-small from cluster default"

        # Same with quiet mode
        capture = run_cli(["-q", "admin", "remove-resource-preset", "cpu-large"])
        assert not capture.err
        assert not capture.out


def test_remove_resource_preset_not_exists(run_cli: _RunCli) -> None:
    with ExitStack() as exit_stack:
        admin_mocked = exit_stack.enter_context(
            mock.patch.object(_Admin, "update_cluster_resource_presets")
        )
        config_mocked = exit_stack.enter_context(mock.patch.object(Config, "fetch"))

        async def update_cluster_resource_presets(
            cluster_name: str, presets: Mapping[str, Preset]
        ) -> None:
            pass

        async def fetch() -> None:
            pass

        admin_mocked.side_effect = update_cluster_resource_presets
        config_mocked.side_effect = fetch

        capture = run_cli(["admin", "remove-resource-preset", "unknown"])
        assert capture.code
        assert "Preset 'unknown' not found" in capture.err
