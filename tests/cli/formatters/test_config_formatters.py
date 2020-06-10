import textwrap
from dataclasses import replace
from pathlib import Path
from sys import platform
from typing import Callable

import click
import toml

from neuromation.api import Client, Cluster, Preset
from neuromation.api.admin import _Quota
from neuromation.api.quota import _QuotaInfo
from neuromation.cli.alias import list_aliases
from neuromation.cli.formatters.config import (
    AliasesFormatter,
    ConfigFormatter,
    QuotaFormatter,
    QuotaInfoFormatter,
)
from neuromation.cli.root import Root


class TestConfigFormatter:
    async def test_output(self, root: Root) -> None:
        out = ConfigFormatter()(root.client)
        if platform == "win32":
            no = "No"
        else:
            no = "✖︎"
        assert "\n".join(
            line.rstrip() for line in click.unstyle(out).splitlines()
        ) == textwrap.dedent(
            f"""\
            User Configuration:
              User Name: user
              Current Cluster: default
              API URL: https://dev.neu.ro/api/v1
              Docker Registry URL: https://registry-dev.neu.ro
              Resource Presets:
                Name       #CPU  Memory  Preemptible  GPU
                gpu-small     7   30.0G       {no}      1 x nvidia-tesla-k80
                gpu-large     7   60.0G       {no}      1 x nvidia-tesla-v100
                cpu-small     7    2.0G       {no}
                cpu-large     7   14.0G       {no}"""
        )

    async def test_output_for_tpu_presets(
        self, make_client: Callable[..., Client], cluster_config: Cluster
    ) -> None:
        presets = dict(cluster_config.presets)

        presets["tpu-small"] = Preset(
            cpu=2,
            memory_mb=2048,
            is_preemptible=False,
            tpu_type="v3-8",
            tpu_software_version="1.14",
        )
        presets["hybrid"] = Preset(
            cpu=4,
            memory_mb=30720,
            is_preemptible=False,
            gpu=2,
            gpu_model="nvidia-tesla-v100",
            tpu_type="v3-64",
            tpu_software_version="1.14",
        )
        new_config = replace(cluster_config, presets=presets)

        client = make_client(
            "https://dev.neu.ro/api/v1", clusters={new_config.name: new_config}
        )
        out = ConfigFormatter()(client)
        if platform == "win32":
            yes = "Yes"
            no = "No"
        else:
            yes = " ✔︎"
            no = "✖︎"

        assert "\n".join(
            line.rstrip() for line in click.unstyle(out).splitlines()
        ) == textwrap.dedent(
            f"""\
            User Configuration:
              User Name: user
              Current Cluster: default
              API URL: https://dev.neu.ro/api/v1
              Docker Registry URL: https://registry-dev.neu.ro
              Resource Presets:
                Name         #CPU  Memory  Preemptible  GPU                    TPU
                gpu-small       7   30.0G       {no}      1 x nvidia-tesla-k80
                gpu-large       7   60.0G       {no}      1 x nvidia-tesla-v100
                cpu-small       7    2.0G       {no}
                cpu-large       7   14.0G       {no}
                cpu-large-p     7   14.0G      {yes}
                tpu-small       2    2.0G       {no}                             v3-8/1.14
                hybrid          4   30.0G       {no}      2 x nvidia-tesla-v100  v3-64/1.14"""  # noqa: E501, ignore line length
        )


bold_start = "\x1b[1m"
bold_end = "\x1b[0m"


class TestQuotaInfoFormatter:
    def test_output(self) -> None:
        quota = _QuotaInfo(
            cluster_name="default",
            gpu_time_spent=0.0,
            gpu_time_limit=0.0,
            cpu_time_spent=float((9 * 60 + 19) * 60),
            cpu_time_limit=float((9 * 60 + 39) * 60),
        )
        out = QuotaInfoFormatter()(quota)
        assert out == "\n".join(
            [
                f"{bold_start}GPU:{bold_end} spent: 00h 00m "
                "(quota: 00h 00m, left: 00h 00m)",
                f"{bold_start}CPU:{bold_end} spent: 09h 19m "
                "(quota: 09h 39m, left: 00h 20m)",
            ]
        )

    def test_output_no_quota(self) -> None:
        quota = _QuotaInfo(
            cluster_name="default",
            gpu_time_spent=0.0,
            gpu_time_limit=float("inf"),
            cpu_time_spent=float((9 * 60 + 19) * 60),
            cpu_time_limit=float("inf"),
        )
        out = QuotaInfoFormatter()(quota)
        assert out == "\n".join(
            [
                f"{bold_start}GPU:{bold_end} spent: 00h 00m (quota: infinity)",
                f"{bold_start}CPU:{bold_end} spent: 09h 19m (quota: infinity)",
            ]
        )

    def test_output_too_many_hours(self) -> None:
        quota = _QuotaInfo(
            cluster_name="default",
            gpu_time_spent=float((1 * 60 + 29) * 60),
            gpu_time_limit=float((9 * 60 + 59) * 60),
            cpu_time_spent=float((9999 * 60 + 29) * 60),
            cpu_time_limit=float((99999 * 60 + 59) * 60),
        )
        out = QuotaInfoFormatter()(quota)
        assert out == "\n".join(
            [
                f"{bold_start}GPU:{bold_end} spent: 01h 29m "
                "(quota: 09h 59m, left: 08h 30m)",
                f"{bold_start}CPU:{bold_end} spent: 9999h 29m "
                "(quota: 99999h 59m, left: 90000h 30m)",
            ]
        )

    def test_output_spent_more_than_quota_left_zero(self) -> None:
        quota = _QuotaInfo(
            cluster_name="default",
            gpu_time_spent=float(9 * 60 * 60),
            gpu_time_limit=float(1 * 60 * 60),
            cpu_time_spent=float(9 * 60 * 60),
            cpu_time_limit=float(2 * 60 * 60),
        )
        out = QuotaInfoFormatter()(quota)
        assert out == "\n".join(
            [
                f"{bold_start}GPU:{bold_end} spent: 09h 00m "
                "(quota: 01h 00m, left: 00h 00m)",
                f"{bold_start}CPU:{bold_end} spent: 09h 00m "
                "(quota: 02h 00m, left: 00h 00m)",
            ]
        )

    def test_format_time_00h_00m(self) -> None:
        out = QuotaInfoFormatter()._format_time(total_seconds=float(0 * 60))
        assert out == "00h 00m"

    def test_format_time_00h_09m(self) -> None:
        out = QuotaInfoFormatter()._format_time(total_seconds=float(9 * 60))
        assert out == "00h 09m"

    def test_format_time_01h_00m(self) -> None:
        out = QuotaInfoFormatter()._format_time(total_seconds=float(60 * 60))
        assert out == "01h 00m"

    def test_format_time_01h_10m(self) -> None:
        out = QuotaInfoFormatter()._format_time(total_seconds=float(70 * 60))
        assert out == "01h 10m"

    def test_format_time_99h_00m(self) -> None:
        out = QuotaInfoFormatter()._format_time(total_seconds=float(99 * 60 * 60))
        assert out == "99h 00m"

    def test_format_time_99h_59m(self) -> None:
        out = QuotaInfoFormatter()._format_time(
            total_seconds=float((99 * 60 + 59) * 60)
        )
        assert out == "99h 59m"

    def test_format_time_9999h_59m(self) -> None:
        out = QuotaInfoFormatter()._format_time(
            total_seconds=float((9999 * 60 + 59) * 60)
        )
        assert out == "9999h 59m"


class TestQuotaFormatter:
    def test_output(self) -> None:
        quota = _Quota(
            total_gpu_run_time_minutes=321, total_non_gpu_run_time_minutes=123,
        )
        out = QuotaFormatter()(quota)
        assert out == "\n".join(
            [f"{bold_start}GPU:{bold_end} 321m", f"{bold_start}CPU:{bold_end} 123m"]
        )

    def test_output_no_quota(self) -> None:
        quota = _Quota(
            total_non_gpu_run_time_minutes=None, total_gpu_run_time_minutes=None
        )
        out = QuotaFormatter()(quota)
        assert out == "\n".join(
            [
                f"{bold_start}GPU:{bold_end} infinity",
                f"{bold_start}CPU:{bold_end} infinity",
            ]
        )

    def test_output_only_gpu(self) -> None:
        quota = _Quota(
            total_gpu_run_time_minutes=9923, total_non_gpu_run_time_minutes=None
        )
        out = QuotaFormatter()(quota)
        assert out == "\n".join(
            [
                f"{bold_start}GPU:{bold_end} 9923m",
                f"{bold_start}CPU:{bold_end} infinity",
            ]
        )

    def test_output_only_cpu(self) -> None:
        quota = _Quota(
            total_non_gpu_run_time_minutes=3256, total_gpu_run_time_minutes=None
        )
        out = QuotaFormatter()(quota)
        assert out == "\n".join(
            [
                f"{bold_start}GPU:{bold_end} infinity",
                f"{bold_start}CPU:{bold_end} 3256m",
            ]
        )

    def test_output_zeroes(self) -> None:
        quota = _Quota(total_gpu_run_time_minutes=0, total_non_gpu_run_time_minutes=0)
        out = QuotaFormatter()(quota)
        assert out == "\n".join(
            [f"{bold_start}GPU:{bold_end} 0m", f"{bold_start}CPU:{bold_end} 0m"]
        )


class TestAliasesFormatter:
    async def test_output(self, root: Root, nmrc_path: Path) -> None:
        user_cfg = nmrc_path / "user.toml"
        user_cfg.write_text(
            toml.dumps(
                {
                    "alias": {
                        "lsl": {
                            "cmd": "storage ls -l",
                            "help": "Custom ls with long output.",
                        },
                        "user-cmd": {"exec": "script"},
                    }
                }
            )
        )
        lst = await list_aliases(root)
        out = AliasesFormatter()(lst)
        assert "\n".join(
            click.unstyle(line).rstrip() for line in out
        ) == textwrap.dedent(
            """\
            Alias     Description
            lsl       Custom ls with long output.
            user-cmd  script"""
        )
