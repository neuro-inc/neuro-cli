import operator
from typing import Iterable, List, Mapping, Optional

import click
from rich import box
from rich.console import RenderableType, RenderGroup
from rich.padding import Padding
from rich.table import Table

from neuromation.api import Cluster, Config, Preset
from neuromation.api.admin import _Quota
from neuromation.api.quota import _QuotaInfo
from neuromation.cli.utils import format_size


class ConfigFormatter:
    def __call__(
        self, config: Config, available_jobs_counts: Mapping[str, int]
    ) -> RenderableType:
        lines: List[RenderableType] = []
        lines.append("[b]User Configuration[/b]:")
        lines.append(f"  [b]User Name[/b]: {config.username}")
        lines.append(f"  [b]Current Cluster[/b]: {config.cluster_name}")
        lines.append(f"  [b]API URL[/b]: {config.api_url}")
        lines.append(f"  [b]Docker Registry URL[/b]: {config.registry_url}")
        lines.append(f"  [b]Resource Presets[/b]:")
        lines.append(
            Padding.indent(_format_presets(config.presets, available_jobs_counts), 4)
        )
        return RenderGroup(*lines)


class QuotaInfoFormatter:
    QUOTA_NOT_SET = "infinity"

    def __call__(self, quota: _QuotaInfo) -> RenderableType:
        gpu_details = self._format_quota_details(
            quota.gpu_time_spent, quota.gpu_time_limit, quota.gpu_time_left
        )
        cpu_details = self._format_quota_details(
            quota.cpu_time_spent, quota.cpu_time_limit, quota.cpu_time_left
        )
        return RenderGroup(f"[b]GPU:[/b] {gpu_details}", f"[b]CPU[/b]: {cpu_details}")

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
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours:02d}h {minutes:02d}m"


class QuotaFormatter:
    QUOTA_NOT_SET = "infinity"

    def __call__(self, quota: _Quota) -> RenderableType:
        gpu_details = self._format_quota_details(quota.total_gpu_run_time_minutes)
        non_gpu_details = self._format_quota_details(
            quota.total_non_gpu_run_time_minutes
        )
        return RenderGroup(
            f"[b]GPU[/b]: {gpu_details}", f"[b]CPU[/b]: {non_gpu_details}"
        )

    def _format_quota_details(self, run_time_minutes: Optional[int]) -> str:
        if run_time_minutes is None:
            return self.QUOTA_NOT_SET
        else:
            return f"{run_time_minutes}m"


class ClustersFormatter:
    def __call__(
        self, clusters: Iterable[Cluster], default_name: Optional[str]
    ) -> RenderableType:
        out: List[RenderableType] = ["[b]Available clusters:[/b]"]
        for cluster in clusters:
            name = cluster.name or ""
            if cluster.name == default_name:
                name = f"[u]{name}[/u]"
            pre = "* " if cluster.name == default_name else "  "
            out.append(pre + "[b]Name[/b]: " + name)
            out.append("  [b]Presets[/b]:")
            out.append(Padding.indent(_format_presets(cluster.presets, None), 4))
        return RenderGroup(*out)


def _format_presets(
    presets: Mapping[str, Preset],
    available_jobs_counts: Optional[Mapping[str, int]],
) -> Table:
    has_tpu = False
    for preset in presets.values():
        if preset.tpu_type:
            has_tpu = True
            break

    table = Table(box=box.MINIMAL_HEAVY_HEAD)
    table.add_column("Name", style="bold", justify="left")
    table.add_column("#CPU", justify="right")
    table.add_column("Memory", justify="right")
    table.add_column("Preemptible", justify="center")
    table.add_column("GPU", justify="left")
    if available_jobs_counts:
        table.add_column("Jobs Avail", justify="right")
    if has_tpu:
        table.add_column("TPU", justify="left")

    for name, preset in presets.items():
        gpu = ""
        if preset.gpu:
            gpu = f"{preset.gpu} x {preset.gpu_model}"
        row = [
            name,
            str(preset.cpu),
            format_size(preset.memory_mb * 1024 ** 2),
            "√" if preset.is_preemptible else "×",
            gpu,
        ]
        if has_tpu:
            tpu = (
                f"{preset.tpu_type}/{preset.tpu_software_version}"
                if preset.tpu_type
                else ""
            )
            row.append(tpu)
        if available_jobs_counts:
            if name in available_jobs_counts:
                row.append(str(available_jobs_counts[name]))
            else:
                row.append("")
        table.add_row(*row)

    return table


class AliasesFormatter:
    def __call__(self, aliases: Iterable[click.Command]) -> Table:
        table = Table(box=box.MINIMAL_HEAVY_HEAD)
        table.add_column("Alias", style="bold")
        table.add_column("Description")
        for alias in sorted(aliases, key=operator.attrgetter("name")):
            table.add_row(alias.name, alias.get_short_help_str())
        return table
