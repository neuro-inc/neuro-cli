from typing import Callable

from aiohttp import web
from aiohttp.web import HTTPCreated, HTTPNoContent
from aiohttp.web_exceptions import HTTPOk

from neuromation.api import Client
from neuromation.api.admin import (
    _CloudProvider,
    _Cluster,
    _ClusterUser,
    _ClusterUserRoleType,
    _NodePool,
    _Storage,
)
from tests import _TestServerFactory


_MakeClient = Callable[..., Client]


async def test_list_clusters(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handle_list_clusters(request: web.Request) -> web.StreamResponse:
        assert request.query["include"] == "cloud_provider_infra"
        data = [
            {"name": "default", "status": "deployed"},
            {"name": "other", "status": "deployed"},
        ]
        return web.json_response(data)

    app = web.Application()
    app.router.add_get("/api/v1/clusters", handle_list_clusters)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/api/v1")) as client:
        clusters = await client._admin.list_clusters()
        assert clusters == {
            "default": _Cluster(name="default", status="deployed"),
            "other": _Cluster(name="other", status="deployed"),
        }


async def test_list_clusters_with_cloud_provider(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handle_list_clusters(request: web.Request) -> web.StreamResponse:
        assert request.query["include"] == "cloud_provider_infra"
        data = [
            {
                "name": "default",
                "status": "deployed",
                "cloud_provider": {
                    "type": "gcp",
                    "region": "us-central1",
                    "zone": "us-central1-a",
                    "node_pools": [
                        {
                            "machine_type": "n1-highmem-8",
                            "min_size": 1,
                            "max_size": 2,
                            "idle_size": 1,
                            "available_cpu": 7,
                            "available_memory_mb": 46080,
                            "gpu": 1,
                            "gpu_model": "nvidia-tesla-k80",
                            "is_tpu_enabled": True,
                            "is_preemptible": True,
                        },
                        {
                            "machine_type": "n1-highmem-8",
                            "min_size": 1,
                            "max_size": 2,
                            "available_cpu": 7,
                            "available_memory_mb": 46080,
                        },
                    ],
                    "storage": {"description": "Filestore"},
                },
            },
            {
                "name": "on-prem",
                "status": "deployed",
                "cloud_provider": {
                    "type": "on_prem",
                    "node_pools": [
                        {
                            "min_size": 2,
                            "max_size": 2,
                            "machine_type": "n1-highmem-8",
                            "available_cpu": 7,
                            "available_memory_mb": 46080,
                        },
                    ],
                    "storage": {"description": "NFS"},
                },
            },
            {
                "name": "other1",
                "status": "deployed",
                "cloud_provider": {
                    "type": "gcp",
                    "region": "us-central1",
                    "zones": ["us-central1-a", "us-central1-c"],
                },
            },
            {
                "name": "other2",
                "status": "deployed",
                "cloud_provider": {"type": "aws", "region": "us-central1"},
            },
        ]
        return web.json_response(data)

    app = web.Application()
    app.router.add_get("/api/v1/clusters", handle_list_clusters)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/api/v1")) as client:
        clusters = await client._admin.list_clusters()
        assert clusters == {
            "default": _Cluster(
                name="default",
                status="deployed",
                cloud_provider=_CloudProvider(
                    type="gcp",
                    region="us-central1",
                    zones=["us-central1-a"],
                    node_pools=[
                        _NodePool(
                            min_size=1,
                            max_size=2,
                            idle_size=1,
                            machine_type="n1-highmem-8",
                            available_cpu=7.0,
                            available_memory_mb=46080,
                            gpu=1,
                            gpu_model="nvidia-tesla-k80",
                            is_tpu_enabled=True,
                            is_preemptible=True,
                        ),
                        _NodePool(
                            min_size=1,
                            max_size=2,
                            machine_type="n1-highmem-8",
                            available_cpu=7.0,
                            available_memory_mb=46080,
                        ),
                    ],
                    storage=_Storage(description="Filestore"),
                ),
            ),
            "on-prem": _Cluster(
                name="on-prem",
                status="deployed",
                cloud_provider=_CloudProvider(
                    type="on_prem",
                    region=None,
                    zones=[],
                    node_pools=[
                        _NodePool(
                            min_size=2,
                            max_size=2,
                            machine_type="n1-highmem-8",
                            available_cpu=7.0,
                            available_memory_mb=46080,
                        ),
                    ],
                    storage=_Storage(description="NFS"),
                ),
            ),
            "other1": _Cluster(
                name="other1",
                status="deployed",
                cloud_provider=_CloudProvider(
                    type="gcp",
                    region="us-central1",
                    zones=["us-central1-a", "us-central1-c"],
                    node_pools=[],
                    storage=None,
                ),
            ),
            "other2": _Cluster(
                name="other2",
                status="deployed",
                cloud_provider=_CloudProvider(
                    type="aws",
                    region="us-central1",
                    zones=[],
                    node_pools=[],
                    storage=None,
                ),
            ),
        }


async def test_add_cluster(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    create_cluster_json = None
    put_cloud_json = None
    # GCP cloud provider example from
    # https://github.com/neuromation/platform-config#configuring-cloud-provider
    JSON = {
        "type": "gcp",
        "location_type": "zonal",
        "region": "us-central1",
        "zone": "us-central1-a",
        "project": "project",
        "credentials": {
            "type": "service_account",
            "project_id": "project_id",
            "private_key_id": "private_key_id",
            "private_key": "private_key",
            "client_email": "service.account@gmail.com",
            "client_id": "client_id",
            "auth_uri": "https://auth_uri",
            "token_uri": "https://token_uri",
            "auth_provider_x509_cert_url": "https://auth_provider_x509_cert_url",
            "client_x509_cert_url": "https://client_x509_cert_url",
        },
        "node_pools": [
            {
                "id": "n1_highmem_8",  # id of the GCP node pool template
                "min_size": 0,
                "max_size": 5,
                "is_tpu_enabled": True,
            },
            {"id": "n1_highmem_32_4x_nvidia_tesla_k80", "min_size": 0, "max_size": 5},
            {
                "id": "n1_highmem_32_4x_nvidia_tesla_k80",
                "min_size": 0,
                "max_size": 5,
                "is_preemptible": True,
            },
        ],
        "storage": {
            "id": "premium",  # id of the GCP storage template
            "capacity_tb": 2.5,
        },
    }

    async def handle_create_cluster(request: web.Request) -> web.StreamResponse:
        nonlocal create_cluster_json
        create_cluster_json = await request.json()
        return web.Response(status=201)

    async def handle_put_cloud_provider(request: web.Request) -> web.StreamResponse:
        nonlocal put_cloud_json
        assert request.query["start_deployment"] == "true"
        put_cloud_json = await request.json()
        return web.Response(status=201)

    app = web.Application()
    app.router.add_post("/apis/admin/v1/clusters", handle_create_cluster)
    app.router.add_put(
        "/api/v1/clusters/default/cloud_provider", handle_put_cloud_provider
    )

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/api/v1")) as client:
        await client._admin.add_cluster("default", JSON)

    assert create_cluster_json == {"name": "default"}
    assert put_cloud_json == JSON


async def test_list_cluster_users_explicit_cluster(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    requested_clusters = []

    async def handle_list_cluster_user(request: web.Request) -> web.StreamResponse:
        requested_clusters.append(request.match_info["cluster_name"])
        data = [
            {"user_name": "denis", "role": "admin"},
            {"user_name": "andrew", "role": "manager"},
            {"user_name": "ivan", "role": "user"},
        ]
        return web.json_response(data)

    app = web.Application()
    app.router.add_get(
        "/apis/admin/v1/clusters/{cluster_name}/users", handle_list_cluster_user
    )

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/api/v1")) as client:
        resp = await client._admin.list_cluster_users("my_cluster")
        assert resp == [
            _ClusterUser(user_name="denis", role=_ClusterUserRoleType("admin")),
            _ClusterUser(user_name="andrew", role=_ClusterUserRoleType("manager")),
            _ClusterUser(user_name="ivan", role=_ClusterUserRoleType("user")),
        ]
        assert requested_clusters == ["my_cluster"]


async def test_list_cluster_users_default_cluster(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    requested_clusters = []

    async def handle_list_cluster_user(request: web.Request) -> web.StreamResponse:
        requested_clusters.append(request.match_info["cluster_name"])
        data = [
            {"user_name": "denis", "role": "admin"},
            {"user_name": "andrew", "role": "manager"},
            {"user_name": "ivan", "role": "user"},
        ]
        return web.json_response(data)

    app = web.Application()
    app.router.add_get(
        "/apis/admin/v1/clusters/{cluster_name}/users", handle_list_cluster_user
    )

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/api/v1")) as client:
        resp = await client._admin.list_cluster_users()
        assert resp == [
            _ClusterUser(user_name="denis", role=_ClusterUserRoleType("admin")),
            _ClusterUser(user_name="andrew", role=_ClusterUserRoleType("manager")),
            _ClusterUser(user_name="ivan", role=_ClusterUserRoleType("user")),
        ]
        assert requested_clusters == ["default"]


async def test_add_cluster_user(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    requested_clusters = []
    requested_payloads = []

    async def handle_add_cluster_user(request: web.Request) -> web.StreamResponse:
        payload = await request.json()
        requested_clusters.append(request.match_info["cluster_name"])
        requested_payloads.append(payload)
        return web.json_response(payload, status=HTTPCreated.status_code)

    app = web.Application()
    app.router.add_post(
        "/apis/admin/v1/clusters/{cluster_name}/users", handle_add_cluster_user
    )

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/api/v1")) as client:
        resp = await client._admin.add_cluster_user("default", "ivan", "user")
        assert resp == _ClusterUser(user_name="ivan", role=_ClusterUserRoleType("user"))
        assert requested_clusters == ["default"]
        assert requested_payloads == [{"role": "user", "user_name": "ivan"}]


async def test_remove_cluster_user(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    requested_cluster_users = []

    async def handle_remove_cluster_user(request: web.Request) -> web.StreamResponse:
        requested_cluster_users.append(
            (request.match_info["cluster_name"], request.match_info["user_name"],)
        )
        return web.Response(status=HTTPNoContent.status_code)

    app = web.Application()
    app.router.add_delete(
        "/apis/admin/v1/clusters/{cluster_name}/users/{user_name}",
        handle_remove_cluster_user,
    )

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/api/v1")) as client:
        await client._admin.remove_cluster_user("default", "ivan")
        assert requested_cluster_users == [("default", "ivan")]


async def test_set_user_quota(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    requested_cluster_users = []
    requested_payloads = []

    async def handle_cluster_user_quota_patch(
        request: web.Request,
    ) -> web.StreamResponse:
        requested_cluster_users.append(
            (request.match_info["cluster_name"], request.match_info["user_name"],)
        )
        payload = await request.json()
        requested_payloads.append(dict(payload))
        payload["role"] = "user"
        return web.json_response(payload, status=HTTPOk.status_code)

    app = web.Application()
    app.router.add_patch(
        "/apis/admin/v1/clusters/{cluster_name}/users/{user_name}/quota",
        handle_cluster_user_quota_patch,
    )

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/api/v1")) as client:
        await client._admin.set_user_quota("default", "ivan", 100, 200)
        await client._admin.set_user_quota("neuro", "user2", None, None)
        await client._admin.set_user_quota("neuro-ai", "user3", 150, None)
        assert requested_cluster_users == [
            ("default", "ivan"),
            ("neuro", "user2"),
            ("neuro-ai", "user3"),
        ]
        assert len(requested_payloads) == 3
        assert {
            "quota": {
                "total_gpu_run_time_minutes": 100,
                "total_non_gpu_run_time_minutes": 200,
            },
        } in requested_payloads
        assert {"quota": {}} in requested_payloads
        assert {"quota": {"total_gpu_run_time_minutes": 150}} in requested_payloads


async def test_add_user_quota(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    requested_cluster_users = []
    requested_payloads = []

    async def handle_cluster_user_quota_patch(
        request: web.Request,
    ) -> web.StreamResponse:
        requested_cluster_users.append(
            (request.match_info["cluster_name"], request.match_info["user_name"],)
        )
        payload = await request.json()
        requested_payloads.append(dict(payload))
        payload["role"] = "user"
        return web.json_response(payload, status=HTTPOk.status_code)

    app = web.Application()
    app.router.add_patch(
        "/apis/admin/v1/clusters/{cluster_name}/users/{user_name}/quota",
        handle_cluster_user_quota_patch,
    )

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/api/v1")) as client:
        await client._admin.add_user_quota("default", "ivan", 100, 200)
        await client._admin.add_user_quota("neuro", "user2", None, None)
        await client._admin.add_user_quota("neuro-ai", "user3", 150, None)
        assert requested_cluster_users == [
            ("default", "ivan"),
            ("neuro", "user2"),
            ("neuro-ai", "user3"),
        ]
        assert len(requested_payloads) == 3
        assert {
            "additional_quota": {
                "total_gpu_run_time_minutes": 100,
                "total_non_gpu_run_time_minutes": 200,
            },
        } in requested_payloads
        assert {"additional_quota": {}} in requested_payloads
        assert {
            "additional_quota": {"total_gpu_run_time_minutes": 150},
        } in requested_payloads
