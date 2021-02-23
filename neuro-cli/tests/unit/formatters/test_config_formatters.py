from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Callable

import toml
from rich.console import RenderableType

from neuro_sdk import Client, Cluster, Preset
from neuro_sdk.admin import _Quota
from neuro_sdk.quota import _QuotaInfo

from neuro_cli.alias import list_aliases
from neuro_cli.formatters.config import (
    AliasesFormatter,
    ConfigFormatter,
    QuotaFormatter,
    QuotaInfoFormatter,
)
from neuro_cli.root import Root

RichCmp = Callable[[RenderableType], None]


class TestConfigFormatter:
    async def test_output(self, root: Root, rich_cmp: RichCmp) -> None:
        out = ConfigFormatter()(root.client.config, {})
        rich_cmp(out)

    async def test_output_for_tpu_presets(
        self,
        make_client: Callable[..., Client],
        cluster_config: Cluster,
        rich_cmp: RichCmp,
    ) -> None:
        presets = dict(cluster_config.presets)

        presets["tpu-small"] = Preset(
            credits_per_hour=Decimal("10"),
            cpu=2,
            memory_mb=2048,
            scheduler_enabled=False,
            tpu_type="v3-8",
            tpu_software_version="1.14",
        )
        presets["hybrid"] = Preset(
            credits_per_hour=Decimal("10"),
            cpu=4,
            memory_mb=30720,
            scheduler_enabled=False,
            gpu=2,
            gpu_model="nvidia-tesla-v100",
            tpu_type="v3-64",
            tpu_software_version="1.14",
        )
        new_config = replace(cluster_config, presets=presets)

        client = make_client(
            "https://dev.neu.ro/api/v1", clusters={new_config.name: new_config}
        )
        out = ConfigFormatter()(client.config, {})
        rich_cmp(out)
        await client.close()

    async def test_output_with_jobs_available(
        self, root: Root, rich_cmp: RichCmp
    ) -> None:
        available_jobs_counts = {
            "cpu-small": 1,
            "cpu-large": 2,
        }
        out = ConfigFormatter()(root.client.config, available_jobs_counts)
        rich_cmp(out)


bold_start = "\x1b[1m"
bold_end = "\x1b[0m"


class TestQuotaInfoFormatter:
    def test_output(self, rich_cmp: RichCmp) -> None:
        quota = _QuotaInfo(
            cluster_name="default",
            gpu_time_spent=0.0,
            gpu_time_limit=0.0,
            cpu_time_spent=float((9 * 60 + 19) * 60),
            cpu_time_limit=float((9 * 60 + 39) * 60),
        )
        out = QuotaInfoFormatter()(quota)
        rich_cmp(out)

    def test_output_no_quota(self, rich_cmp: RichCmp) -> None:
        quota = _QuotaInfo(
            cluster_name="default",
            gpu_time_spent=0.0,
            gpu_time_limit=float("inf"),
            cpu_time_spent=float((9 * 60 + 19) * 60),
            cpu_time_limit=float("inf"),
        )
        out = QuotaInfoFormatter()(quota)
        rich_cmp(out)

    def test_output_too_many_hours(self, rich_cmp: RichCmp) -> None:
        quota = _QuotaInfo(
            cluster_name="default",
            gpu_time_spent=float((1 * 60 + 29) * 60),
            gpu_time_limit=float((9 * 60 + 59) * 60),
            cpu_time_spent=float((9999 * 60 + 29) * 60),
            cpu_time_limit=float((99999 * 60 + 59) * 60),
        )
        out = QuotaInfoFormatter()(quota)
        rich_cmp(out)

    def test_output_spent_more_than_quota_left_zero(self, rich_cmp: RichCmp) -> None:
        quota = _QuotaInfo(
            cluster_name="default",
            gpu_time_spent=float(9 * 60 * 60),
            gpu_time_limit=float(1 * 60 * 60),
            cpu_time_spent=float(9 * 60 * 60),
            cpu_time_limit=float(2 * 60 * 60),
        )
        out = QuotaInfoFormatter()(quota)
        rich_cmp(out)

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
    def test_output(self, rich_cmp: RichCmp) -> None:
        quota = _Quota(
            credits=Decimal("10"),
            total_running_jobs=10,
            total_gpu_run_time_minutes=321,
            total_non_gpu_run_time_minutes=123,
        )
        out = QuotaFormatter()(quota)
        rich_cmp(out)

    def test_output_no_quota(self, rich_cmp: RichCmp) -> None:
        quota = _Quota(
            credits=None,
            total_running_jobs=None,
            total_non_gpu_run_time_minutes=None,
            total_gpu_run_time_minutes=None,
        )
        out = QuotaFormatter()(quota)
        rich_cmp(out)

    def test_output_only_gpu(self, rich_cmp: RichCmp) -> None:
        quota = _Quota(
            credits=None,
            total_running_jobs=None,
            total_gpu_run_time_minutes=9923,
            total_non_gpu_run_time_minutes=None,
        )
        out = QuotaFormatter()(quota)
        rich_cmp(out)

    def test_output_only_cpu(self, rich_cmp: RichCmp) -> None:
        quota = _Quota(
            credits=None,
            total_running_jobs=None,
            total_non_gpu_run_time_minutes=3256,
            total_gpu_run_time_minutes=None,
        )
        out = QuotaFormatter()(quota)
        rich_cmp(out)

    def test_output_only_jobs(self, rich_cmp: RichCmp) -> None:
        quota = _Quota(
            credits=None,
            total_running_jobs=10,
            total_non_gpu_run_time_minutes=None,
            total_gpu_run_time_minutes=None,
        )
        out = QuotaFormatter()(quota)
        rich_cmp(out)

    def test_output_only_credits(self, rich_cmp: RichCmp) -> None:
        quota = _Quota(
            credits=Decimal("10"),
            total_running_jobs=10,
            total_non_gpu_run_time_minutes=None,
            total_gpu_run_time_minutes=None,
        )
        out = QuotaFormatter()(quota)
        rich_cmp(out)

    def test_output_zeroes(self, rich_cmp: RichCmp) -> None:
        quota = _Quota(
            credits=Decimal("0"),
            total_running_jobs=0,
            total_gpu_run_time_minutes=0,
            total_non_gpu_run_time_minutes=0,
        )
        out = QuotaFormatter()(quota)
        rich_cmp(out)


class TestAliasesFormatter:
    async def test_output(self, root: Root, nmrc_path: Path, rich_cmp: RichCmp) -> None:
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
        rich_cmp(out)
