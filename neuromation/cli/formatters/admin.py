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
        rows = [headers]

        for user in clusters_users:
            rows.append((user.user_name, user.role.value))

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
                out.append(prefix + style("Cloud: ", bold=True) + cloud_provider.type)
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
    has_tpu = _has_tpu(node_pools)
    has_idle = _has_idle(node_pools)

    headers = ["Machine", "CPU", "Memory", "Preemptible", "GPU"]
    if has_tpu:
        headers.append("TPU")
    headers.append("Min")
    headers.append("Max")
    if has_idle:
        headers.append("Idle")

    rows = [headers]

    for node_pool in node_pools:
        row = [
            node_pool.machine_type,
            str(node_pool.available_cpu),
            format_size(node_pool.available_memory_mb * 1024 ** 2),
            _yes() if node_pool.is_preemptible else _no(),
            _gpu(node_pool),
        ]
        if has_tpu:
            row.append(_yes() if node_pool.is_tpu_enabled else _no())
        row.append(str(node_pool.min_size))
        row.append(str(node_pool.max_size))
        if has_idle:
            row.append(str(node_pool.idle_size))
        rows.append(row)

    aligns = [Align.LEFT, Align.RIGHT, Align.RIGHT, Align.CENTER, Align.RIGHT]
    if has_tpu:
        aligns.append(Align.RIGHT)
    aligns.append(Align.RIGHT)
    aligns.append(Align.RIGHT)
    if has_idle:
        aligns.append(Align.RIGHT)

    for line in table(rows=rows, aligns=aligns):
        yield prefix + line


def _yes() -> str:
    return "Yes" if sys.platform == "win32" else "✔︎"


def _no() -> str:
    return "No" if sys.platform == "win32" else "✖︎"


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
