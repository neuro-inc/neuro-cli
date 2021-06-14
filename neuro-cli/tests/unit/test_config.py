import sys
from decimal import Decimal
from pathlib import Path
from typing import Callable
from unittest import mock

import pytest
from yarl import URL

from neuro_sdk import Client, Cluster, Preset

from neuro_cli.config import prompt_cluster
from neuro_cli.root import Root


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Promt_toolkit fails in github actions worker",
)
def test_prompt_cluster(make_client: Callable[..., Client]) -> None:
    clusters = {
        "first": Cluster(
            registry_url=URL("https://registry-dev.neu.ro"),
            storage_url=URL("https://storage-dev.neu.ro"),
            blob_storage_url=URL("https://blob-storage-dev.neu.ro"),
            users_url=URL("https://users-dev.neu.ro"),
            monitoring_url=URL("https://monitoring-dev.neu.ro"),
            secrets_url=URL("https://secrets-dev.neu.ro"),
            disks_url=URL("https://disks-dev.neu.ro"),
            presets={
                "cpu-small": Preset(
                    credits_per_hour=Decimal("10"), cpu=1, memory_mb=1024
                )
            },
            name="first",
        ),
        "second": Cluster(
            registry_url=URL("https://registry2-dev.neu.ro"),
            storage_url=URL("https://storage2-dev.neu.ro"),
            blob_storage_url=URL("https://blob-storage2-dev.neu.ro"),
            users_url=URL("https://users2-dev.neu.ro"),
            monitoring_url=URL("https://monitoring2-dev.neu.ro"),
            secrets_url=URL("https://secrets2-dev.neu.ro"),
            disks_url=URL("https://disks2-dev.neu.ro"),
            presets={
                "cpu-small": Preset(
                    credits_per_hour=Decimal("10"), cpu=2, memory_mb=1024
                )
            },
            name="second",
        ),
    }

    root = Root(
        color=False,
        tty=False,
        disable_pypi_version_check=True,
        network_timeout=60,
        config_path=Path("<config-path>"),
        verbosity=0,
        trace=False,
        trace_hide_token=True,
        force_trace_all=False,
        command_path="",
        command_params=[],
        skip_gmp_stats=True,
        show_traceback=False,
        iso_datetime_format=False,
    )

    async def _async_make_client() -> Client:
        return make_client("https://neu.ro", clusters=clusters)

    root._client = root.run(_async_make_client())

    session = mock.Mock()
    loop = root._runner._loop
    fut = loop.create_future()
    fut.set_result("second")
    session.prompt_async.return_value = fut
    ret = root.run(prompt_cluster(root, session=session))
    assert ret == "second"
    root.close()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Promt_toolkit fails in github actions worker",
)
def test_prompt_cluster_default(make_client: Callable[..., Client]) -> None:
    clusters = {
        "first": Cluster(
            registry_url=URL("https://registry-dev.neu.ro"),
            storage_url=URL("https://storage-dev.neu.ro"),
            blob_storage_url=URL("https://blob-storage-dev.neu.ro"),
            users_url=URL("https://users-dev.neu.ro"),
            monitoring_url=URL("https://monitoring-dev.neu.ro"),
            secrets_url=URL("https://secrets-dev.neu.ro"),
            disks_url=URL("https://disks-dev.neu.ro"),
            presets={
                "cpu-small": Preset(
                    credits_per_hour=Decimal("10"), cpu=1, memory_mb=1024
                )
            },
            name="first",
        ),
        "second": Cluster(
            registry_url=URL("https://registry2-dev.neu.ro"),
            storage_url=URL("https://storage2-dev.neu.ro"),
            blob_storage_url=URL("https://blob-storage2-dev.neu.ro"),
            users_url=URL("https://users2-dev.neu.ro"),
            monitoring_url=URL("https://monitoring2-dev.neu.ro"),
            secrets_url=URL("https://secrets2-dev.neu.ro"),
            disks_url=URL("https://disks2-dev.neu.ro"),
            presets={
                "cpu-small": Preset(
                    credits_per_hour=Decimal("10"), cpu=2, memory_mb=1024
                )
            },
            name="second",
        ),
    }

    root = Root(
        color=False,
        tty=False,
        disable_pypi_version_check=True,
        network_timeout=60,
        config_path=Path("<config-path>"),
        verbosity=0,
        trace=False,
        trace_hide_token=True,
        force_trace_all=False,
        command_path="",
        command_params=[],
        skip_gmp_stats=True,
        show_traceback=False,
        iso_datetime_format=False,
    )

    async def _async_make_client() -> Client:
        return make_client("https://neu.ro", clusters=clusters)

    root._client = root.run(_async_make_client())

    session = mock.Mock()
    loop = root._runner._loop
    fut = loop.create_future()
    fut.set_result("")
    session.prompt_async.return_value = fut

    ret = root.run(prompt_cluster(root, session=session))
    assert ret == "first"
    root.close()
