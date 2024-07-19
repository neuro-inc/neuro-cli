from typing import Callable

from aiohttp import web

from apolo_sdk import Client

from tests import _TestServerFactory

_MakeClient = Callable[..., Client]


async def test_add_cluster(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    create_cluster_json = None
    put_cloud_json = None
    # GCP cloud provider example from
    # https://github.com/neuro-inc/platform-config#configuring-cloud-provider
    JSON = {
        "type": "gcp",
        "location_type": "zonal",
        "region": "us-central1",
        "zone": "us-central1-a",
        "project": "project",
        "tpu_enabled": True,
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
            "instances": [{"size": 1024 * 2**20}],
        },
    }

    async def handle_create_cluster(request: web.Request) -> web.StreamResponse:
        nonlocal create_cluster_json
        create_cluster_json = await request.json()
        return web.json_response(create_cluster_json, status=201)

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
        await client._admin.create_cluster("default")
        await client._clusters.setup_cluster_cloud_provider("default", JSON)

    assert create_cluster_json == {
        "name": "default",
        "default_quota": {},
        "default_role": "user",
        "maintenance": False,
    }
    assert put_cloud_json == JSON
