from typing import Callable
from unittest import mock

from aiohttp import web
from yarl import URL

from neuromation.api import Client, ClusterConfig, Preset
from tests import _TestServerFactory


_MakeClient = Callable[..., Client]


async def test_username(aiohttp_server: _TestServerFactory, make_client: _MakeClient):
    app = web.Application()
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        assert client.config.username == "user"


async def test_presets(aiohttp_server: _TestServerFactory, make_client: _MakeClient):
    app = web.Application()
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        assert client.config.presets == {
            "cpu-large": Preset(
                cpu=7,
                memory_mb=14336,
                is_preemptible=False,
                gpu=None,
                gpu_model=None,
                tpu_type=None,
                tpu_software_version=None,
            ),
            "cpu-small": Preset(
                cpu=7,
                memory_mb=2048,
                is_preemptible=False,
                gpu=None,
                gpu_model=None,
                tpu_type=None,
                tpu_software_version=None,
            ),
            "gpu-large": Preset(
                cpu=7,
                memory_mb=61440,
                is_preemptible=False,
                gpu=1,
                gpu_model="nvidia-tesla-v100",
                tpu_type=None,
                tpu_software_version=None,
            ),
            "gpu-small": Preset(
                cpu=7,
                memory_mb=30720,
                is_preemptible=False,
                gpu=1,
                gpu_model="nvidia-tesla-k80",
                tpu_type=None,
                tpu_software_version=None,
            ),
        }


async def test_cluster_name(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
):
    app = web.Application()
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        assert client.config.cluster_name == "default"


async def test_clusters(aiohttp_server: _TestServerFactory, make_client: _MakeClient):
    app = web.Application()
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        assert client.config.clusters == {
            "default": ClusterConfig(
                name="default",
                registry_url=URL("https://registry-dev.neu.ro"),
                storage_url=srv.make_url("/storage"),
                users_url=srv.make_url("/"),
                monitoring_url=srv.make_url("/jobs"),
                resource_presets=mock.ANY,
            )
        }
