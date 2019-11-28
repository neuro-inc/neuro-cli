import sys
from typing import Iterable, Iterator, List, Mapping, Optional

from click import style

from neuromation.api import ClusterConfig, Preset
from neuromation.api.quota import _QuotaInfo
from neuromation.cli.root import Root
from neuromation.cli.utils import format_size

from .ftable import Align, table


class ConfigFormatter:
    def __call__(self, root: Root) -> str:
        lines = []
        lines.append(style("User Name", bold=True) + f": {root.username}")
        lines.append(style("Current Cluster", bold=True) + f": {root.cluster_name}")
        lines.append(style("API URL", bold=True) + f": {root.url}")
        lines.append(style("Docker Registry URL", bold=True) + f": {root.registry_url}")
        lines.append(style("Resource Presets", bold=True) + f":")
        indent: str = "  "
        return (
            style("User Configuration", bold=True)
            + ":\n"
            + indent
            + f"\n{indent}".join(lines)
            + "\n"
            + f"\n".join(_format_presets(root.resource_presets, "    "))
        )


class QuotaInfoFormatter:
    QUOTA_NOT_SET = "infinity"

    def __call__(self, quota: _QuotaInfo) -> str:
        gpu_details = self._format_quota_details(
            quota.gpu_time_spent, quota.gpu_time_limit, quota.gpu_time_left
        )
        cpu_details = self._format_quota_details(
            quota.cpu_time_spent, quota.cpu_time_limit, quota.cpu_time_left
        )
        return (
            f"{style('GPU:', bold=True)}"
            f" {gpu_details}"
            "\n"
            f"{style('CPU:', bold=True)}"
            f" {cpu_details}"
        )

    def _format_quota_details(
        self, time_spent: float, time_limit: float, time_left: float
    ) -> str:
        spent_str = f"spent: {self._format_time(time_spent)}"
        quota_str = "quota: "
        if time_limit < float("inf"):
            assert time_left < float("inf")
            quota_str += self._format_time(time_limit)
            quota_str += f", left: {self._format_time(time_left)}"
        else:
            quota_str += self.QUOTA_NOT_SET
        return f"{spent_str} ({quota_str})"

    def _format_time(self, total_seconds: float) -> str:
        # Since API for `GET /stats/users/{name}` returns time in minutes,
        #  we need to display it in minutes as well.
        total_minutes = int(total_seconds // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        minutes_zero_padded = "{0:02d}m".format(minutes)
        hours_zero_padded = "{0:02d}".format(hours)
        hours_space_padded = f"{hours_zero_padded:>2}h"
        return f"{hours_space_padded} {minutes_zero_padded}"


class ClustersFormatter:
    def __call__(
        self, clusters: Iterable[ClusterConfig], default_name: Optional[str]
    ) -> List[str]:
        out = [style("Available clusters:", bold=True)]
        for cluster in clusters:
            name = cluster.name or ""
            if cluster.name == default_name:
                name = style(name, underline=True)
            pre = "* " if cluster.name == default_name else "  "
            out.append(pre + style("Name: ", bold=True) + name)
            out.append(style("  Presets:", bold=True))
            out.extend(_format_presets(cluster.resource_presets, "    "))
        return out


def _format_presets(presets: Mapping[str, Preset], prefix: str) -> Iterator[str]:
    if sys.platform == "win32":
        yes, no = "Yes", "No"
    else:
        yes, no = "✔︎", "✖︎"
    has_tpu = False
    for preset in presets.values():
        if preset.tpu_type:
            has_tpu = True
            break

    rows = []
    headers = ["Name", "#CPU", "Memory", "Preemptible", "GPU"]
    # TODO: support ANSI styles in headers
    # headers = [style(name, bold=True) for name in headers]
    rows.append(headers)
    if has_tpu:
        headers.append("TPU")

    for name, preset in presets.items():
        gpu = ""
        if preset.gpu:
            gpu = f"{preset.gpu} x {preset.gpu_model}"
        row = [
            name,
            str(preset.cpu),
            format_size(preset.memory_mb * 1024 ** 2),
            yes if preset.is_preemptible else no,
            gpu,
        ]
        if has_tpu:
            tpu = (
                f"{preset.tpu_type}/{preset.tpu_software_version}"
                if preset.tpu_type
                else ""
            )
            row.append(tpu)
        rows.append(row)
    for line in table(
        rows=rows, aligns=[Align.LEFT, Align.RIGHT, Align.RIGHT, Align.CENTER]
    ):
        yield prefix + line
