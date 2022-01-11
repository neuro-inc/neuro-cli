from decimal import Decimal
from typing import Callable

from dateutil.parser import isoparse
from rich.console import RenderableType

from neuro_sdk import (
    _Balance,
    _CloudProvider,
    _Cluster,
    _ClusterUserRoleType,
    _ClusterUserWithInfo,
    _ConfigCluster,
    _NodePool,
    _Quota,
    _Storage,
    _UserInfo,
)

from neuro_cli.formatters.admin import ClustersFormatter, ClusterUserFormatter

RichCmp = Callable[[RenderableType], None]


class TestClusterUserFormatter:
    def test_cluster_list(self, rich_cmp: RichCmp) -> None:
        formatter = ClusterUserFormatter()
        users = [
            _ClusterUserWithInfo(
                user_name="denis",
                cluster_name="default",
                org_name=None,
                role=_ClusterUserRoleType("admin"),
                quota=_Quota(),
                balance=_Balance(),
                user_info=_UserInfo(
                    first_name="denis",
                    last_name="admin",
                    email="denis@domain.name",
                    created_at=isoparse("2017-03-04T12:28:59.759433+00:00"),
                ),
            ),
            _ClusterUserWithInfo(
                user_name="andrew",
                cluster_name="default",
                org_name=None,
                role=_ClusterUserRoleType("manager"),
                quota=_Quota(),
                balance=_Balance(credits=Decimal(100)),
                user_info=_UserInfo(
                    first_name="andrew",
                    last_name=None,
                    email="andrew@domain.name",
                    created_at=isoparse("2017-03-04T12:28:59.759433+00:00"),
                ),
            ),
            _ClusterUserWithInfo(
                user_name="ivan",
                cluster_name="default",
                org_name=None,
                role=_ClusterUserRoleType("user"),
                quota=_Quota(total_running_jobs=1),
                balance=_Balance(),
                user_info=_UserInfo(
                    first_name=None,
                    last_name="user",
                    email="ivan@domain.name",
                    created_at=isoparse("2017-03-04T12:28:59.759433+00:00"),
                ),
            ),
            _ClusterUserWithInfo(
                user_name="alex",
                cluster_name="default",
                org_name=None,
                role=_ClusterUserRoleType("user"),
                quota=_Quota(total_running_jobs=2),
                balance=_Balance(credits=Decimal(100), spent_credits=Decimal(20)),
                user_info=_UserInfo(
                    first_name=None,
                    last_name=None,
                    email="alex@domain.name",
                    created_at=None,
                ),
            ),
        ]
        rich_cmp(formatter(users))


class TestClustersFormatter:
    def _create_node_pool(
        self,
        disk_type: str = "",
        is_scalable: bool = True,
        is_gpu: bool = False,
        is_tpu_enabled: bool = False,
        is_preemptible: bool = False,
        has_idle: bool = False,
    ) -> _NodePool:
        return _NodePool(
            min_size=1 if is_scalable else 2,
            max_size=2,
            idle_size=1 if has_idle else 0,
            machine_type="n1-highmem-8",
            available_cpu=7.0,
            available_memory_mb=46080,
            disk_size_gb=150,
            disk_type=disk_type,
            gpu=1 if is_gpu else 0,
            gpu_model="nvidia-tesla-k80" if is_gpu else None,
            is_preemptible=is_preemptible,
            is_tpu_enabled=is_tpu_enabled,
        )

    def test_cluster_list(self, rich_cmp: RichCmp) -> None:
        formatter = ClustersFormatter()
        clusters = {
            "default": (
                _Cluster(
                    name="default",
                    default_credits=Decimal(20),
                    default_quota=_Quota(total_running_jobs=42),
                ),
                _ConfigCluster(name="default", status="deployed"),
            )
        }
        rich_cmp(formatter(clusters))

    def test_cluster_with_on_prem_cloud_provider_list(self, rich_cmp: RichCmp) -> None:
        formatter = ClustersFormatter()
        clusters = {
            "on-prem": (
                _Cluster(name="on-prem", default_credits=None, default_quota=_Quota()),
                _ConfigCluster(
                    name="on-prem",
                    status="deployed",
                    cloud_provider=_CloudProvider(
                        type="on_prem",
                        region=None,
                        zones=[],
                        node_pools=[],
                        storage=None,
                    ),
                ),
            )
        }
        rich_cmp(formatter(clusters))

    def test_cluster_with_cloud_provider_storage_list(self, rich_cmp: RichCmp) -> None:
        formatter = ClustersFormatter()
        clusters = {
            "default": (
                _Cluster(name="default", default_credits=None, default_quota=_Quota()),
                _ConfigCluster(
                    name="default",
                    status="deployed",
                    cloud_provider=_CloudProvider(
                        type="gcp",
                        region="us-central1",
                        zones=["us-central1-a", "us-central1-c"],
                        node_pools=[],
                        storage=_Storage(description="Filestore"),
                    ),
                ),
            )
        }
        rich_cmp(formatter(clusters))

    def test_cluster_with_cloud_provider_with_minimum_node_pool_properties_list(
        self, rich_cmp: RichCmp
    ) -> None:
        formatter = ClustersFormatter()
        clusters = {
            "default": (
                _Cluster(name="default", default_credits=None, default_quota=_Quota()),
                _ConfigCluster(
                    name="default",
                    status="deployed",
                    cloud_provider=_CloudProvider(
                        type="on_prem",
                        region=None,
                        zones=[],
                        node_pools=[
                            self._create_node_pool(disk_type="", is_scalable=False),
                            self._create_node_pool(
                                disk_type="ssd", is_scalable=False, is_gpu=True
                            ),
                        ],
                        storage=None,
                    ),
                ),
            )
        }
        rich_cmp(formatter(clusters))

    def test_cluster_with_cloud_provider_with_maximum_node_pool_properties_list(
        self, rich_cmp: RichCmp
    ) -> None:
        formatter = ClustersFormatter()
        clusters = {
            "default": (
                _Cluster(name="default", default_credits=None, default_quota=_Quota()),
                _ConfigCluster(
                    name="default",
                    status="deployed",
                    cloud_provider=_CloudProvider(
                        type="gcp",
                        region="us-central1",
                        zones=[],
                        node_pools=[
                            self._create_node_pool(
                                is_preemptible=True, is_tpu_enabled=True, has_idle=True
                            ),
                            self._create_node_pool(),
                        ],
                        storage=None,
                    ),
                ),
            )
        }
        rich_cmp(formatter(clusters))
