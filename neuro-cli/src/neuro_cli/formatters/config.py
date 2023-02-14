import calendar
import operator
from datetime import time
from decimal import Decimal
from typing import Iterable, List, Mapping, Optional, Sequence, Union

import click
from rich import box
from rich.console import Group as RichGroup
from rich.console import RenderableType
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

from neuro_sdk import Cluster, Config, Preset, Quota, _Balance, _ConfigCluster, _Quota

from neuro_cli.click_types import OrgType
from neuro_cli.utils import format_size


class ConfigFormatter:
    def __call__(
        self,
        config: Config,
        available_jobs_counts: Mapping[str, int],
        quota: Quota,
        org_quota: Optional[Quota],
        config_cluster: Optional[_ConfigCluster] = None,
    ) -> RenderableType:
        table = Table(
            title="User Configuration:",
            title_justify="left",
            box=None,
            show_header=False,
            show_edge=False,
        )
        table.add_column()
        table.add_column(style="bold")
        table.add_row("User Name", config.username)
        table.add_row("Current Cluster", config.cluster_name)
        table.add_row("Current Org", config.org_name or "<no-org>")
        table.add_row("Credits Quota", format_quota_details(quota.credits))
        table.add_row("Jobs Quota", format_quota_details(quota.total_running_jobs))
        if org_quota:
            table.add_row("Org Credits Quota", format_quota_details(org_quota.credits))
            table.add_row(
                "Org Jobs Quota", format_quota_details(org_quota.total_running_jobs)
            )
        table.add_row("API URL", str(config.api_url))
        table.add_row("Docker Registry URL", str(config.registry_url))

        to_render = [table, _format_presets(config.presets, available_jobs_counts)]
        if config_cluster and config_cluster.energy:
            to_render.extend(_format_cluster_energy(config_cluster))  # type: ignore
        return RichGroup(*to_render)


class AdminQuotaFormatter:
    def __call__(self, quota: _Quota) -> RenderableType:
        jobs_details = format_quota_details(quota.total_running_jobs)
        return RichGroup(
            Text.assemble(Text("Jobs", style="bold"), f": ", jobs_details),
        )


class BalanceFormatter:
    def __call__(self, balance: _Balance) -> RenderableType:
        credits_details = format_quota_details(balance.credits)
        spent_credits_details = format_quota_details(balance.spent_credits)
        return RichGroup(
            Text.assemble(Text("Credits", style="bold"), f": ", credits_details),
            Text.assemble(
                Text("Credits spent", style="bold"), f": ", spent_credits_details
            ),
        )


class ClustersFormatter:
    def __call__(
        self,
        clusters: Iterable[Cluster],
        default_cluster: Optional[str],
        default_org: Optional[str],
    ) -> RenderableType:
        out: List[RenderableType] = [Text("Available clusters:", style="i")]
        for cluster in clusters:
            name: Union[str, Text] = cluster.name or ""
            pre = "  "
            org_names: List[Text] = [
                Text(org or OrgType.NO_ORG_STR, style="u")
                if org == default_org and cluster.name == default_cluster
                else Text(org or OrgType.NO_ORG_STR)
                for org in cluster.orgs
            ]
            if cluster.name == default_cluster:
                name = Text(cluster.name, style="u")
                pre = "* "
            out.append(Text.assemble(pre, Text("Name"), ": ", name))
            out.append(
                Text.assemble("  ", Text("Orgs"), ": ", Text(", ").join(org_names))
            )
            out.append(Padding.indent(_format_presets(cluster.presets, None), 2))
        return RichGroup(*out)


def _format_presets(
    presets: Mapping[str, Preset],
    available_jobs_counts: Optional[Mapping[str, int]],
) -> Table:
    has_tpu = False
    for preset in presets.values():
        if preset.tpu_type:
            has_tpu = True
            break

    table = Table(
        title="Resource Presets:",
        title_justify="left",
        box=box.SIMPLE_HEAVY,
        show_edge=False,
    )
    table.add_column("Name", style="bold", justify="left")
    table.add_column("#CPU", justify="right")
    table.add_column("Memory", justify="right")
    table.add_column("Round Robin", justify="center")
    table.add_column("Preemptible Node", justify="center")
    table.add_column("GPU", justify="left")
    if available_jobs_counts:
        table.add_column("Jobs Avail", justify="right")
    if has_tpu:
        table.add_column("TPU", justify="left")
    table.add_column("Credits per hour", justify="left")

    for name, preset in presets.items():
        gpu = ""
        if preset.gpu:
            gpu = f"{preset.gpu} x {preset.gpu_model}"
        row = [
            name,
            str(preset.cpu),
            format_size(preset.memory),
            "√" if preset.scheduler_enabled else "×",
            "√" if preset.preemptible_node else "×",
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
        row.append(str(preset.credits_per_hour))
        table.add_row(*row)

    return table


def _format_cluster_energy(cluster: _ConfigCluster) -> Sequence[RenderableType]:
    assert cluster.energy

    summary = [
        Text("Cluster energy parameters:", style="i"),
        Text.assemble(
            Text("CO2 eq g/kWh: "),
            Text(str(cluster.energy.co2_grams_eq_per_kwh), style="b"),
        ),
    ]

    schedules_tbl = Table(
        title="Energy schedules:",
        title_justify="left",
        box=box.SIMPLE_HEAVY,
        show_edge=False,
    )
    schedules_tbl.add_column("Name", style="bold", justify="left")
    schedules_tbl.add_column("Price (kW/h)", justify="center")
    schedules_tbl.add_column("Start time", justify="center")
    schedules_tbl.add_column("End time", justify="center")
    schedules_tbl.add_column("Weekday", justify="center")
    for schedule in cluster.energy.schedules:
        joint_periods: dict[tuple[time, time], list[int]] = {}
        for period in schedule.periods:
            key = (period.start_time, period.end_time)
            if key not in joint_periods:
                joint_periods[key] = []
            joint_periods[key].append(period.weekday)

        for timeslot, days in sorted(joint_periods.items(), key=lambda x: x[1]):
            schedules_tbl.add_row(
                str(schedule.name),
                str(schedule.price_per_kwh),
                timeslot[0].strftime("%H:%M"),
                timeslot[1].strftime("%H:%M"),
                ", ".join([calendar.day_abbr[x - 1] for x in sorted(days)]),
            )
    return *summary, schedules_tbl


class AliasesFormatter:
    def __call__(self, aliases: Iterable[click.Command]) -> Table:
        table = Table(box=box.MINIMAL_HEAVY_HEAD)
        table.add_column("Alias", style="bold")
        table.add_column("Description")
        for alias in sorted(aliases, key=operator.attrgetter("name")):
            table.add_row(alias.name, alias.get_short_help_str())
        return table


_QUOTA_NOT_SET = "unlimited"


def format_quota_details(quota: Optional[Union[int, Decimal]]) -> str:
    if quota is None:
        return _QUOTA_NOT_SET
    elif isinstance(quota, Decimal):
        return f"{quota:.2f}"
    else:
        return str(quota)
