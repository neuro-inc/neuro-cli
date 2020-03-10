import operator
import sys
from typing import Iterable, Iterator, List

import click
from click import style

from neuromation.api.admin import _Cluster, _ClusterUser, _NodePool
from neuromation.cli.utils import format_size

from .ftable import Align, table


class ClusterUserFormatter:
    def __call__(self, clusters_users: Iterable[_ClusterUser]) -> List[str]:
        headers = (click.style("Name", bold=True), click.style("Role", bold=True))
        rows = []

        for user in clusters_users:
            rows.append((user.user_name, user.role.value))
        rows.sort(key=operator.itemgetter(0))

        rows.insert(0, headers)
        return list(table(rows=rows))


class ClustersFormatter:
    def __call__(self, clusters: Iterable[_Cluster]) -> List[str]:
        out = []
        for cluster in clusters:
            prefix = "  "
            out.append(style(f"{cluster.name}:", bold=True))
            out.append(
                prefix + style("Status: ", bold=True) + cluster.status.capitalize()
            )
            if cluster.cloud_provider:
                cloud_provider = cluster.cloud_provider
                if cloud_provider.type != "on_prem":
                    out.append(
                        prefix + style("Cloud: ", bold=True) + cloud_provider.type
                    )
                if cloud_provider.region:
                    out.append(
                        prefix + style("Region: ", bold=True) + cloud_provider.region
                    )
                if cloud_provider.zones:
                    out.append(
                        prefix
                        + style("Zones: ", bold=True)
                        + ", ".join(cloud_provider.zones)
                    )
                if cloud_provider.node_pools:
                    out.append(prefix + style("Node pools:", bold=True))
                    out.extend(
                        _format_node_pools(cloud_provider.node_pools, prefix + "  ")
                    )
                if cloud_provider.storage:
                    out.append(
                        prefix
                        + style("Storage: ", bold=True)
                        + cloud_provider.storage.description
                    )
        return out


def _format_node_pools(node_pools: Iterable[_NodePool], prefix: str) -> Iterator[str]:
    is_scalable = _is_scalable(node_pools)
    has_preemptible = _has_preemptible(node_pools)
    has_tpu = _has_tpu(node_pools)
    has_idle = _has_idle(node_pools)

    headers = ["Machine", "CPU", "Memory"]
    if has_preemptible:
        headers.append("Preemptible")
    headers.append("GPU")
    if has_tpu:
        headers.append("TPU")
    if is_scalable:
        headers.append("Min")
        headers.append("Max")
    else:
        headers.append("Size")
    if has_idle:
        headers.append("Idle")

    rows = [headers]
    for node_pool in node_pools:
        row = [
            node_pool.machine_type,
            str(node_pool.available_cpu),
            format_size(node_pool.available_memory_mb * 1024 ** 2),
        ]
        if has_preemptible:
            row.append(_yes() if node_pool.is_preemptible else _no())
        row.append(_gpu(node_pool))
        if has_tpu:
            row.append(_yes() if node_pool.is_tpu_enabled else _no())
        if is_scalable:
            row.append(str(node_pool.min_size))
        row.append(str(node_pool.max_size))
        if has_idle:
            row.append(str(node_pool.idle_size))
        rows.append(row)

    aligns = [Align.LEFT, Align.RIGHT, Align.RIGHT]
    if has_preemptible:
        aligns.append(Align.CENTER)
    aligns.append(Align.RIGHT)
    if has_tpu:
        aligns.append(Align.CENTER)
    aligns.append(Align.RIGHT)
    if is_scalable:
        aligns.append(Align.RIGHT)
    if has_idle:
        aligns.append(Align.RIGHT)

    for line in table(rows=rows, aligns=aligns):
        yield prefix + line


def _yes() -> str:
    return "Yes" if sys.platform == "win32" else "✔︎"


def _no() -> str:
    return "No" if sys.platform == "win32" else "✖︎"


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
