from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Callable, Union

import pytest
import toml
from rich.console import RenderableType

from neuro_sdk import Client, Cluster, Preset, Quota, _Balance, _Quota

from neuro_cli.alias import list_aliases
from neuro_cli.formatters.config import (
    AdminQuotaFormatter,
    AliasesFormatter,
    BalanceFormatter,
    ConfigFormatter,
    format_quota_details,
)
from neuro_cli.root import Root

RichCmp = Callable[[RenderableType], None]


@pytest.mark.parametrize(
    "quota,expected",
    [
        pytest.param(None, "unlimited", id="None->infinity"),
        pytest.param(0, "0", id="zero"),
        pytest.param(10, "10", id="int"),
        pytest.param(Decimal("1.23456"), "1.23", id="decimal"),
    ],
)
def test_format_quota_details(quota: Union[None, int, Decimal], expected: str) -> None:
    assert format_quota_details(quota) == expected


class TestConfigFormatter:
    async def test_output(self, root: Root, rich_cmp: RichCmp) -> None:
        out = ConfigFormatter()(
            root.client.config, {}, Quota(credits=Decimal("500"), total_running_jobs=10)
        )
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
        out = ConfigFormatter()(
            client.config, {}, Quota(credits=Decimal("500"), total_running_jobs=10)
        )
        rich_cmp(out)
        await client.close()

    async def test_output_with_jobs_available(
        self, root: Root, rich_cmp: RichCmp
    ) -> None:
        available_jobs_counts = {
            "cpu-small": 1,
            "cpu-large": 2,
        }
        out = ConfigFormatter()(
            root.client.config,
            available_jobs_counts,
            Quota(credits=Decimal("500"), total_running_jobs=10),
        )
        rich_cmp(out)


bold_start = "\x1b[1m"
bold_end = "\x1b[0m"


class TestAdminQuotaFormatter:
    def test_output(self, rich_cmp: RichCmp) -> None:
        quota = _Quota(
            total_running_jobs=10,
        )
        out = AdminQuotaFormatter()(quota)
        rich_cmp(out)

    def test_output_no_quota(self, rich_cmp: RichCmp) -> None:
        quota = _Quota(
            total_running_jobs=None,
        )
        out = AdminQuotaFormatter()(quota)
        rich_cmp(out)

    def test_output_zeroes(self, rich_cmp: RichCmp) -> None:
        quota = _Quota(
            total_running_jobs=0,
        )
        out = AdminQuotaFormatter()(quota)
        rich_cmp(out)


class TestBalanceFormatter:
    def test_output(self, rich_cmp: RichCmp) -> None:
        balance = _Balance(credits=Decimal("10"), spent_credits=Decimal("0.23"))
        out = BalanceFormatter()(balance)
        rich_cmp(out)

    def test_output_no_quota(self, rich_cmp: RichCmp) -> None:
        balance = _Balance(
            credits=None,
        )
        out = BalanceFormatter()(balance)
        rich_cmp(out)

    def test_output_rounding(self, rich_cmp: RichCmp) -> None:
        balance = _Balance(credits=Decimal("10"), spent_credits=Decimal(1 / 3))
        out = BalanceFormatter()(balance)
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
