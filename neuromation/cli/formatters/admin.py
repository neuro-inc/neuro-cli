import operator
from typing import Iterable, List

from rich import box
from rich.console import RenderableType, RenderGroup
from rich.padding import Padding
from rich.table import Table

from neuromation.api.admin import _Cluster, _ClusterUser, _NodePool
from neuromation.cli.utils import format_size


class ClusterUserFormatter:
    def __call__(self, clusters_users: Iterable[_ClusterUser]) -> RenderableType:
        table = Table(box=box.MINIMAL_HEAVY_HEAD)
        table.add_column("Name", style="bold")
        table.add_column("Role")
        rows = []

        for user in clusters_users:
            rows.append((user.user_name, user.role.value))
        rows.sort(key=operator.itemgetter(0))

        for row in rows:
            table.add_row(*row)
        return table


class ClustersFormatter:
    def __call__(self, clusters: Iterable[_Cluster]) -> RenderableType:
        out: List[RenderableType] = []
        for cluster in clusters:
            prefix = "  "
            out.append(f"[b]{cluster.name}[/b]:")
            out.append(prefix + "[b]Status[/b]: " + cluster.status.capitalize())
            if cluster.cloud_provider:
                cloud_provider = cluster.cloud_provider
                if cloud_provider.type != "on_prem":
                    out.append(prefix + "[b]Cloud[/b]: " + cloud_provider.type)
                if cloud_provider.region:
                    out.append(prefix + "[b]Region[/b]: " + cloud_provider.region)
                if cloud_provider.zones:
                    out.append(
                        prefix + "[b]Zones[/b]: " + ", ".join(cloud_provider.zones)
                    )
                if cloud_provider.node_pools:
                    out.append(prefix + "[b]Node pools[/b]:")
                    out.append(
                        Padding.indent(_format_node_pools(cloud_provider.node_pools), 4)
                    )
                if cloud_provider.storage:
                    out.append(
                        prefix + "[b]Storage[/b]: " + cloud_provider.storage.description
                    )
        return RenderGroup(*out)


def _format_node_pools(node_pools: Iterable[_NodePool]) -> Table:
    is_scalable = _is_scalable(node_pools)
    has_preemptible = _has_preemptible(node_pools)
    has_tpu = _has_tpu(node_pools)
    has_idle = _has_idle(node_pools)

    table = Table(box=box.MINIMAL_HEAVY_HEAD)
    table.add_column("Machine", style="bold", justify="left")
    table.add_column("CPU", justify="right")
    table.add_column("Memory", justify="right")
    if has_preemptible:
        table.add_column("Preemptible", justify="center")
    table.add_column("GPU", justify="right")
    if has_tpu:
        table.add_column("TPU", justify="center")
    if is_scalable:
        table.add_column("Min", justify="right")
        table.add_column("Max", justify="right")
    else:
        table.add_column("Size", justify="right")
    if has_idle:
        table.add_column("Idle", justify="right")

    for node_pool in node_pools:
        row = [
            node_pool.machine_type,
            str(node_pool.available_cpu),
            format_size(node_pool.available_memory_mb * 1024 ** 2),
        ]
        if has_preemptible:
            row.append("√" if node_pool.is_preemptible else "×")
        row.append(_gpu(node_pool))
        if has_tpu:
            row.append("√" if node_pool.is_tpu_enabled else "×")
        if is_scalable:
            row.append(str(node_pool.min_size))
        row.append(str(node_pool.max_size))
        if has_idle:
            row.append(str(node_pool.idle_size))
        table.add_row(*row)

    return table


def _is_scalable(node_pools: Iterable[_NodePool]) -> bool:
    for node_pool in node_pools:
        if node_pool.min_size != node_pool.max_size:
            return True
    return False


def _has_preemptible(node_pools: Iterable[_NodePool]) -> bool:
    for node_pool in node_pools:
        if node_pool.is_preemptible:
            return True
    return False


def _has_tpu(node_pools: Iterable[_NodePool]) -> bool:
    for node_pool in node_pools:
        if node_pool.is_tpu_enabled:
            return True
    return False


def _has_idle(node_pools: Iterable[_NodePool]) -> bool:
    for node_pool in node_pools:
        if node_pool.idle_size:
            return True
    return False


def _gpu(node_pool: _NodePool) -> str:
    if node_pool.gpu:
        return f"{node_pool.gpu} x {node_pool.gpu_model}"
    return ""
