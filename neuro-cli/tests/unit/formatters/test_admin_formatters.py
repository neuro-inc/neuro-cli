from decimal import Decimal
from typing import Callable

from rich.console import RenderableType

from neuro_sdk.admin import (
    _CloudProvider,
    _Cluster,
    _ClusterUser,
    _ClusterUserRoleType,
    _NodePool,
    _Storage,
)
from neuro_sdk.users import Quota

from neuro_cli.formatters.admin import ClustersFormatter, ClusterUserFormatter

RichCmp = Callable[[RenderableType], None]


class TestClusterUserFormatter:
    def test_cluster_list(self, rich_cmp: RichCmp) -> None:
        formatter = ClusterUserFormatter()
        users = [
            _ClusterUser(
                user_name="denis", role=_ClusterUserRoleType("admin"), quota=Quota()
            ),
            _ClusterUser(
                user_name="andrew",
                role=_ClusterUserRoleType("manager"),
                quota=Quota(credits=Decimal(100)),
            ),
            _ClusterUser(
                user_name="ivan",
                role=_ClusterUserRoleType("user"),
                quota=Quota(total_running_jobs=1),
            ),
            _ClusterUser(
                user_name="alex",
                role=_ClusterUserRoleType("user"),
                quota=Quota(credits=Decimal(10), total_running_jobs=2),
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
        clusters = [_Cluster(name="default", status="deployed")]
        rich_cmp(formatter(clusters))

    def test_cluster_with_on_prem_cloud_provider_list(self, rich_cmp: RichCmp) -> None:
        formatter = ClustersFormatter()
        clusters = [
            _Cluster(
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
        ]
        rich_cmp(formatter(clusters))

    def test_cluster_with_cloud_provider_storage_list(self, rich_cmp: RichCmp) -> None:
        formatter = ClustersFormatter()
        clusters = [
            _Cluster(
                name="default",
                status="deployed",
                cloud_provider=_CloudProvider(
                    type="gcp",
                    region="us-central1",
                    zones=["us-central1-a", "us-central1-c"],
                    node_pools=[],
                    storage=_Storage(description="Filestore"),
                ),
            )
        ]
        rich_cmp(formatter(clusters))

    def test_cluster_with_cloud_provider_with_minimum_node_pool_properties_list(
        self, rich_cmp: RichCmp
    ) -> None:
        formatter = ClustersFormatter()
        clusters = [
            _Cluster(
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
            )
        ]
        rich_cmp(formatter(clusters))

    def test_cluster_with_cloud_provider_with_maximum_node_pool_properties_list(
        self, rich_cmp: RichCmp
    ) -> None:
        formatter = ClustersFormatter()
        clusters = [
            _Cluster(
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
            )
        ]
        rich_cmp(formatter(clusters))
