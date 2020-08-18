import operator
from typing import Iterable, Iterator, List, Mapping, Optional

import click
from click import style

from neuromation.api import Cluster, Config, Preset
from neuromation.api.admin import _Quota
from neuromation.api.quota import _QuotaInfo
from neuromation.cli.utils import format_size

from .ftable import Align, table


class ConfigFormatter:
    def __call__(self, config: Config, available_jobs_counts: Mapping[str, int]) -> str:
        lines = []
        lines.append(style("User Configuration", bold=True) + ":")
        lines.append("  " + style("User Name", bold=True) + f": {config.username}")
        lines.append(
            "  " + style("Current Cluster", bold=True) + f": {config.cluster_name}"
        )
        lines.append("  " + style("API URL", bold=True) + f": {config.api_url}")
        lines.append(
            "  " + style("Docker Registry URL", bold=True) + f": {config.registry_url}"
        )
        lines.append("  " + style("Resource Presets", bold=True) + f":")
        lines.extend(_format_presets(config.presets, available_jobs_counts, "    "))
        return "\n".join(lines)


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
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours:02d}h {minutes:02d}m"


class QuotaFormatter:
    QUOTA_NOT_SET = "infinity"

    def __call__(self, quota: _Quota) -> str:
        gpu_details = self._format_quota_details(quota.total_gpu_run_time_minutes)
        non_gpu_details = self._format_quota_details(
            quota.total_non_gpu_run_time_minutes
        )
        return (
            f"{style('GPU:', bold=True)}"
            f" {gpu_details}"
            "\n"
            f"{style('CPU:', bold=True)}"
            f" {non_gpu_details}"
        )

    def _format_quota_details(self, run_time_minutes: Optional[int]) -> str:
        if run_time_minutes is None:
            return self.QUOTA_NOT_SET
        else:
            return f"{run_time_minutes}m"


class ClustersFormatter:
    def __call__(
        self, clusters: Iterable[Cluster], default_name: Optional[str]
    ) -> List[str]:
        out = [style("Available clusters:", bold=True)]
        for cluster in clusters:
            name = cluster.name or ""
            if cluster.name == default_name:
                name = style(name, underline=True)
            pre = "* " if cluster.name == default_name else "  "
            out.append(pre + style("Name: ", bold=True) + name)
            out.append(style("  Presets:", bold=True))
            out.extend(_format_presets(cluster.presets, None, "    "))
        return out


def _format_presets(
    presets: Mapping[str, Preset],
    available_jobs_counts: Optional[Mapping[str, int]],
    prefix: str,
) -> Iterator[str]:
    has_tpu = False
    for preset in presets.values():
        if preset.tpu_type:
            has_tpu = True
            break

    rows = []
    headers = ["Name", "#CPU", "Memory", "Preemptible", "GPU"]
    if available_jobs_counts:
        headers.append("Jobs Available")
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
        rows.append(row)
    aligns = [Align.LEFT, Align.RIGHT, Align.RIGHT, Align.CENTER, Align.LEFT]
    if available_jobs_counts:
        aligns.append(Align.RIGHT)
    for line in table(rows=rows, aligns=aligns):
        yield prefix + line


class AliasesFormatter:
    def __call__(self, aliases: Iterable[click.Command]) -> Iterator[str]:
        rows = [["Alias", "Description"]]
        for alias in sorted(aliases, key=operator.attrgetter("name")):
            rows.append(
                [click.style(alias.name, bold=True), alias.get_short_help_str()]
            )
        return table(rows)
