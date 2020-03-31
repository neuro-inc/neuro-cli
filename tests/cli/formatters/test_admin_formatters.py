import textwrap
from sys import platform

from neuromation.api.admin import (
    _CloudProvider,
    _Cluster,
    _ClusterUser,
    _ClusterUserRoleType,
    _NodePool,
    _Storage,
)
from neuromation.cli.formatters.admin import ClustersFormatter, ClusterUserFormatter


class TestClusterUserFormatter:
    def test_cluster_list(self) -> None:
        formatter = ClusterUserFormatter()
        users = [
            _ClusterUser(user_name="denis", role=_ClusterUserRoleType("admin")),
            _ClusterUser(user_name="andrew", role=_ClusterUserRoleType("manager")),
            _ClusterUser(user_name="ivan", role=_ClusterUserRoleType("user")),
            _ClusterUser(user_name="alex", role=_ClusterUserRoleType("user")),
        ]
        expected_out = [
            "\x1b[1mName\x1b[0m    \x1b[1mRole\x1b[0m   ",
            "alex    user   ",
            "andrew  manager",
            "denis   admin  ",
            "ivan    user   ",
        ]
        assert formatter(users) == expected_out


class TestClustersFormatter:
    def _create_node_pool(
        self,
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
            gpu=1 if is_gpu else 0,
            gpu_model="nvidia-tesla-k80" if is_gpu else None,
            is_preemptible=is_preemptible,
            is_tpu_enabled=is_tpu_enabled,
        )

    @property
    def _yes(self) -> str:
        return "Yes" if platform == "win32" else " ✔︎"

    @property
    def _no(self) -> str:
        return "No" if platform == "win32" else "✖︎"

    def test_cluster_list(self) -> None:
        formatter = ClustersFormatter()
        clusters = [_Cluster(name="default", status="deployed")]
        expected_out = textwrap.dedent(
            """\
            \x1b[1mdefault:\x1b[0m
              \x1b[1mStatus: \x1b[0mDeployed"""
        )
        assert "\n".join(formatter(clusters)) == expected_out

    def test_cluster_with_on_prem_cloud_provider_list(self) -> None:
        formatter = ClustersFormatter()
        clusters = [
            _Cluster(
                name="on-prem",
                status="deployed",
                cloud_provider=_CloudProvider(
                    type="on_prem", region=None, zones=[], node_pools=[], storage=None,
                ),
            ),
        ]
        expected_out = textwrap.dedent(
            """\
            \x1b[1mon-prem:\x1b[0m
              \x1b[1mStatus: \x1b[0mDeployed"""
        )
        assert "\n".join(formatter(clusters)) == expected_out

    def test_cluster_with_cloud_provider_storage_list(self) -> None:
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
        expected_out = textwrap.dedent(
            """\
            \x1b[1mdefault:\x1b[0m
              \x1b[1mStatus: \x1b[0mDeployed
              \x1b[1mCloud: \x1b[0mgcp
              \x1b[1mRegion: \x1b[0mus-central1
              \x1b[1mZones: \x1b[0mus-central1-a, us-central1-c
              \x1b[1mStorage: \x1b[0mFilestore"""
        )
        assert "\n".join(formatter(clusters)) == expected_out

    def test_cluster_with_cloud_provider_with_minimum_node_pool_properties_list(
        self,
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
                        self._create_node_pool(is_scalable=False),
                        self._create_node_pool(is_scalable=False, is_gpu=True),
                    ],
                    storage=None,
                ),
            )
        ]
        expected_out = textwrap.dedent(
            f"""\
            \x1b[1mdefault:\x1b[0m
              \x1b[1mStatus: \x1b[0mDeployed
              \x1b[1mNode pools:\x1b[0m
                Machine       CPU  Memory                   GPU  Size
                n1-highmem-8  7.0   45.0G                           2
                n1-highmem-8  7.0   45.0G  1 x nvidia-tesla-k80     2"""  # noqa: E501, ignore line length
        )
        assert "\n".join(formatter(clusters)) == expected_out

    def test_cluster_with_cloud_provider_with_maximum_node_pool_properties_list(
        self,
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
        expected_out = textwrap.dedent(
            f"""\
            \x1b[1mdefault:\x1b[0m
              \x1b[1mStatus: \x1b[0mDeployed
              \x1b[1mCloud: \x1b[0mgcp
              \x1b[1mRegion: \x1b[0mus-central1
              \x1b[1mNode pools:\x1b[0m
                Machine       CPU  Memory  Preemptible  GPU  TPU  Min  Max  Idle
                n1-highmem-8  7.0   45.0G      {self._yes}           {self._yes}    1    2     1
                n1-highmem-8  7.0   45.0G       {self._no}            {self._no}    1    2     0"""  # noqa: E501, ignore line length
        )
        assert "\n".join(formatter(clusters)) == expected_out
