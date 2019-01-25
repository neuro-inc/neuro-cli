from aiohttp import web
from yarl import URL

from neuromation.clientv2 import (
    ClientV2,
    Image,
    NetworkPortForwarding,
    Resources,
    TrainResult,
)


async def test_model_train(aiohttp_server, token):
    JSON = {
        "job_id": "job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
        "status": "failed",
        "http_url": "http://my_host:8889",
        "is_preemptible": False,
        "internal_hostname": "internal.hostname",
    }

    async def handler(request):
        data = await request.json()
        assert data == {
            "container": {
                "image": "submit-image-name",
                "command": "submit-command",
                "http": {"port": 8181},
                "ssh": {"port": 22},
                "resources": {
                    "memory_mb": "4G",
                    "cpu": 7.0,
                    "shm": True,
                    "gpu": 1,
                    "gpu_model": "test-gpu-model",
                },
            },
            "dataset_storage_uri": "storage:/~/src",
            "result_storage_uri": "storage:/~/dst",
            "is_preemptible": False,
            "description": "job description",
        }

        return web.json_response(JSON)

    app = web.Application()
    app.router.add_post("/models", handler)

    srv = await aiohttp_server(app)

    network = NetworkPortForwarding({"http": 8181, "ssh": 22})
    resources = Resources.create(7, 1, "test-gpu-model", "4G", True)

    async with ClientV2(srv.make_url("/"), token) as client:
        image = Image(image="submit-image-name", command="submit-command")
        network = NetworkPortForwarding({"http": 8181, "ssh": 22})
        ret = await client.models.train(
            image=image,
            resources=resources,
            network=network,
            dataset=URL("storage:/~/src"),
            results=URL("storage:/~/dst"),
            is_preemptible=False,
            description="job description",
        )

    assert ret == TrainResult.from_api(JSON)
