from typing import Callable
from unittest import mock

import pytest
from aiohttp import web
from yarl import URL

from neuromation.api import Client, Cluster, Preset
from tests import _TestServerFactory


_MakeClient = Callable[..., Client]


async def test_username(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    app = web.Application()
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        assert client.config.username == "user"


async def test_presets(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
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
) -> None:
    app = web.Application()
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        assert client.config.cluster_name == "default"


async def test_clusters(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    app = web.Application()
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        assert client.config.clusters == {
            "default": Cluster(
                name="default",
                registry_url=URL("https://registry-dev.neu.ro"),
                storage_url=srv.make_url("/storage"),
                users_url=srv.make_url("/"),
                monitoring_url=srv.make_url("/jobs"),
                presets=mock.ANY,
            )
        }


async def test_fetch(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    registry_url = "https://registry2-dev.neu.ro"
    storage_url = "https://storage2-dev.neu.ro"
    users_url = "https://users2-dev.neu.ro"
    monitoring_url = "https://jobs2-dev.neu.ro"
    auth_url = "https://dev-neuromation.auth0.com/authorize"
    token_url = "https://dev-neuromation.auth0.com/oauth/token"
    client_id = "this_is_client_id"
    audience = "https://platform.dev.neuromation.io"
    headless_callback_url = "https://dev.neu.ro/oauth/show-code"
    success_redirect_url = "https://platform.neuromation.io"
    JSON = {
        "auth_url": auth_url,
        "token_url": token_url,
        "client_id": client_id,
        "audience": audience,
        "headless_callback_url": headless_callback_url,
        "success_redirect_url": success_redirect_url,
        "clusters": [
            {
                "name": "default",
                "registry_url": registry_url,
                "storage_url": storage_url,
                "users_url": users_url,
                "monitoring_url": monitoring_url,
                "resource_presets": [
                    {"name": "cpu-small", "cpu": 2, "memory_mb": 2 * 1024}
                ],
            }
        ],
    }

    async def handler(request: web.Request) -> web.Response:
        return web.json_response(JSON)

    app = web.Application()
    app.add_routes([web.get("/config", handler)])
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        await client.config.fetch()
        assert client.config.clusters == {
            "default": Cluster(
                name="default",
                registry_url=URL("https://registry2-dev.neu.ro"),
                storage_url=URL("https://storage2-dev.neu.ro"),
                users_url=URL("https://users2-dev.neu.ro"),
                monitoring_url=URL("https://jobs2-dev.neu.ro"),
                presets={
                    "cpu-small": Preset(
                        cpu=2,
                        memory_mb=2048,
                        is_preemptible=False,
                        gpu=None,
                        gpu_model=None,
                        tpu_type=None,
                        tpu_software_version=None,
                    )
                },
            )
        }


async def test_fetch_dropped_selected_cluster(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    # the test returns the same as for valid answer but the cluster name is different
    registry_url = "https://registry2-dev.neu.ro"
    storage_url = "https://storage2-dev.neu.ro"
    users_url = "https://users2-dev.neu.ro"
    monitoring_url = "https://jobs2-dev.neu.ro"
    auth_url = "https://dev-neuromation.auth0.com/authorize"
    token_url = "https://dev-neuromation.auth0.com/oauth/token"
    client_id = "this_is_client_id"
    audience = "https://platform.dev.neuromation.io"
    headless_callback_url = "https://dev.neu.ro/oauth/show-code"
    success_redirect_url = "https://platform.neuromation.io"
    JSON = {
        "auth_url": auth_url,
        "token_url": token_url,
        "client_id": client_id,
        "audience": audience,
        "headless_callback_url": headless_callback_url,
        "success_redirect_url": success_redirect_url,
        "clusters": [
            {
                "name": "another",
                "registry_url": registry_url,
                "storage_url": storage_url,
                "users_url": users_url,
                "monitoring_url": monitoring_url,
                "resource_presets": [
                    {"name": "cpu-small", "cpu": 2, "memory_mb": 2 * 1024}
                ],
            }
        ],
    }

    async def handler(request: web.Request) -> web.Response:
        return web.json_response(JSON)

    app = web.Application()
    app.add_routes([web.get("/config", handler)])
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        with pytest.raises(RuntimeError, match="Cluster default doesn't exist"):
            await client.config.fetch()


async def test_switch_clusters(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    # the test returns the same as for valid answer but the cluster name is different
    JSON = {
        "auth_url": "https://dev-neuromation.auth0.com/authorize",
        "token_url": "https://dev-neuromation.auth0.com/oauth/token",
        "client_id": "this_is_client_id",
        "audience": "https://platform.dev.neuromation.io",
        "headless_callback_url": "https://dev.neu.ro/oauth/show-code",
        "success_redirect_url": "https://platform.neuromation.io",
        "clusters": [
            {
                "name": "default",
                "registry_url": "https://registry-dev.neu.ro",
                "storage_url": "https://storage-dev.neu.ro",
                "users_url": "https://users-dev.neu.ro",
                "monitoring_url": "https://jobs-dev.neu.ro",
                "resource_presets": [
                    {"name": "cpu-small", "cpu": 2, "memory_mb": 2 * 1024}
                ],
            },
            {
                "name": "another",
                "registry_url": "https://registry2-dev.neu.ro",
                "storage_url": "https://storage2-dev.neu.ro",
                "users_url": "https://users2-dev.neu.ro",
                "monitoring_url": "https://jobs2-dev.neu.ro",
                "resource_presets": [
                    {"name": "cpu-small", "cpu": 2, "memory_mb": 2 * 1024}
                ],
            },
        ],
    }

    async def handler(request: web.Request) -> web.Response:
        return web.json_response(JSON)

    app = web.Application()
    app.add_routes([web.get("/config", handler)])
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        await client.config.fetch()
        assert client.config.cluster_name == "default"
        await client.config.switch_cluster("another")
        assert client.config.cluster_name == "another"


async def test_switch_clusters_unknown(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    # the test returns the same as for valid answer but the cluster name is different
    JSON = {
        "auth_url": "https://dev-neuromation.auth0.com/authorize",
        "token_url": "https://dev-neuromation.auth0.com/oauth/token",
        "client_id": "this_is_client_id",
        "audience": "https://platform.dev.neuromation.io",
        "headless_callback_url": "https://dev.neu.ro/oauth/show-code",
        "success_redirect_url": "https://platform.neuromation.io",
        "clusters": [
            {
                "name": "default",
                "registry_url": "https://registry-dev.neu.ro",
                "storage_url": "https://storage-dev.neu.ro",
                "users_url": "https://users-dev.neu.ro",
                "monitoring_url": "https://jobs-dev.neu.ro",
                "resource_presets": [
                    {"name": "cpu-small", "cpu": 2, "memory_mb": 2 * 1024}
                ],
            }
        ],
    }

    async def handler(request: web.Request) -> web.Response:
        return web.json_response(JSON)

    app = web.Application()
    app.add_routes([web.get("/config", handler)])
    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        await client.config.fetch()
        assert client.config.cluster_name == "default"
        with pytest.raises(RuntimeError, match="Cluster another doesn't exist"):
            await client.config.switch_cluster("another")
        assert client.config.cluster_name == "default"
