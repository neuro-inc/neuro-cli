from typing import Callable

from aiohttp import web

from neuromation.api import Client
from neuromation.api.admin import _Cluster, _ClusterUser, _ClusterUserRoleType
from tests import _TestServerFactory


_MakeClient = Callable[..., Client]


async def test_list_cluster_users(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handle_list_cluster_user(request: web.Request) -> web.StreamResponse:
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
        quota = await client._admin.list_cluster_users()
        assert quota == [
            _ClusterUser(user_name="denis", role=_ClusterUserRoleType("admin")),
            _ClusterUser(user_name="andrew", role=_ClusterUserRoleType("manager")),
            _ClusterUser(user_name="ivan", role=_ClusterUserRoleType("user")),
        ]


async def test_list_clusters(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handle_list_clusters(request: web.Request) -> web.StreamResponse:
        data = [
            {"name": "default"},
            {"name": "other"},
        ]
        return web.json_response(data)

    app = web.Application()
    app.router.add_get("/apis/admin/v1/clusters", handle_list_clusters)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/api/v1")) as client:
        clusters = await client._admin.list_clusters()
        assert clusters == {
            "default": _Cluster(name="default"),
            "other": _Cluster(name="other"),
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
                "is_tpu_enabled": True,  # optional field, only CPU node pools can have TPU
            },
            {
                "id": "n1_highmem_32_4x_nvidia_tesla_k80",  # id of the GCP node pool template
                "min_size": 0,
                "max_size": 5,
            },
            {
                "id": "n1_highmem_32_4x_nvidia_tesla_k80",  # id of the GCP node pool template
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
        "/apis/admin/v1/clusters/default/cloud_provider", handle_put_cloud_provider
    )

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/api/v1")) as client:
        await client._admin.add_cluster("default", JSON)

    assert create_cluster_json == {"name": "default"}
    assert put_cloud_json == JSON
