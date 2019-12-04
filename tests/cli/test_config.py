from typing import Callable
from unittest import mock

from yarl import URL

from neuromation.api import Client, Cluster, Preset
from neuromation.cli.config import prompt_cluster


async def test_prompt_cluster(make_client: Callable[..., Client]) -> None:
    clusters = {
        "first": Cluster(
            registry_url=URL("https://registry-dev.neu.ro"),
            storage_url=URL("https://storage-dev.neu.ro"),
            users_url=URL("https://users-dev.neu.ro"),
            monitoring_url=URL("https://monitoring-dev.neu.ro"),
            presets={"cpu-small": Preset(cpu=1, memory_mb=1024)},
            name="first",
        ),
        "second": Cluster(
            registry_url=URL("https://registry2-dev.neu.ro"),
            storage_url=URL("https://storage2-dev.neu.ro"),
            users_url=URL("https://users2-dev.neu.ro"),
            monitoring_url=URL("https://monitoring2-dev.neu.ro"),
            presets={"cpu-small": Preset(cpu=2, memory_mb=1024)},
            name="second",
        ),
    }

    client = make_client("https://neu.ro", clusters=clusters)

    ret = await prompt_cluster(client, prompt=mock.Mock(return_value="second"))
    assert ret == "second"


async def test_prompt_cluster_default(make_client: Callable[..., Client]) -> None:
    clusters = {
        "first": Cluster(
            registry_url=URL("https://registry-dev.neu.ro"),
            storage_url=URL("https://storage-dev.neu.ro"),
            users_url=URL("https://users-dev.neu.ro"),
            monitoring_url=URL("https://monitoring-dev.neu.ro"),
            presets={"cpu-small": Preset(cpu=1, memory_mb=1024)},
            name="first",
        ),
        "second": Cluster(
            registry_url=URL("https://registry2-dev.neu.ro"),
            storage_url=URL("https://storage2-dev.neu.ro"),
            users_url=URL("https://users2-dev.neu.ro"),
            monitoring_url=URL("https://monitoring2-dev.neu.ro"),
            presets={"cpu-small": Preset(cpu=2, memory_mb=1024)},
            name="second",
        ),
    }

    client = make_client("https://neu.ro", clusters=clusters)

    ret = await prompt_cluster(client, prompt=mock.Mock(return_value=""))
    assert ret == "first"


async def test_prompt_cluster_wrong_answer(make_client: Callable[..., Client]) -> None:
    clusters = {
        "first": Cluster(
            registry_url=URL("https://registry-dev.neu.ro"),
            storage_url=URL("https://storage-dev.neu.ro"),
            users_url=URL("https://users-dev.neu.ro"),
            monitoring_url=URL("https://monitoring-dev.neu.ro"),
            presets={"cpu-small": Preset(cpu=1, memory_mb=1024)},
            name="first",
        ),
        "second": Cluster(
            registry_url=URL("https://registry2-dev.neu.ro"),
            storage_url=URL("https://storage2-dev.neu.ro"),
            users_url=URL("https://users2-dev.neu.ro"),
            monitoring_url=URL("https://monitoring2-dev.neu.ro"),
            presets={"cpu-small": Preset(cpu=2, memory_mb=1024)},
            name="second",
        ),
    }

    client = make_client("https://neu.ro", clusters=clusters)

    ret = await prompt_cluster(
        client, prompt=mock.Mock(side_effect=["another", "second"])
    )
    assert ret == "second"
