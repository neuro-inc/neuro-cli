from typing import List

import pytest
from aiohttp import web

from neuromation.client import (
    Client,
    Image,
    JobDescription,
    NetworkPortForwarding,
    ResourceNotFound,
    Resources,
    Volume,
)
from neuromation.client.jobs import JobTelemetry


async def test_jobs_monitor(aiohttp_server, token):
    async def log_stream(request):
        assert request.headers["Accept-Encoding"] == "identity"
        resp = web.StreamResponse()
        resp.enable_chunked_encoding()
        resp.enable_compression(web.ContentCoding.identity)
        await resp.prepare(request)
        for i in range(10):
            await resp.write(b"chunk " + str(i).encode("ascii") + b"\n")
        return resp

    app = web.Application()
    app.router.add_get("/jobs/job-id/log", log_stream)

    srv = await aiohttp_server(app)

    lst = []
    async with Client(srv.make_url("/"), token) as client:
        async for data in client.jobs.monitor("job-id"):
            lst.append(data)

    assert b"".join(lst) == b"".join(
        [
            b"chunk 0\n",
            b"chunk 1\n",
            b"chunk 2\n",
            b"chunk 3\n",
            b"chunk 4\n",
            b"chunk 5\n",
            b"chunk 6\n",
            b"chunk 7\n",
            b"chunk 8\n",
            b"chunk 9\n",
        ]
    )


async def test_monitor_notexistent_job(aiohttp_server, token):
    async def handler(request):
        raise web.HTTPNotFound()

    app = web.Application()
    app.router.add_get("/jobs/job-id/log", handler)

    srv = await aiohttp_server(app)

    lst = []
    async with Client(srv.make_url("/"), token) as client:
        with pytest.raises(ResourceNotFound):
            async for data in client.jobs.monitor("job-id"):
                lst.append(data)
    assert lst == []


async def test_job_top(aiohttp_server, token):
    def get_data_chunk(index):
        return {
            "cpu": 0.5,
            "memory": 50,
            "timestamp": index,
            "gpu_duty_cycle": 50,
            "gpu_memory": 55.6,
        }

    def get_job_telemetry(index):
        return JobTelemetry(
            cpu=0.5, memory=50, timestamp=index, gpu_duty_cycle=50, gpu_memory=55.6
        )

    async def top_stream(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        for i in range(10):
            await ws.send_json(get_data_chunk(i))

        await ws.close()
        return ws

    app = web.Application()
    app.router.add_get("/jobs/job-id/top", top_stream)

    srv = await aiohttp_server(app)

    lst = []
    async with Client(srv.make_url("/"), token) as client:
        async for data in client.jobs.top("job-id"):
            lst.append(data)

    assert lst == [get_job_telemetry(i) for i in range(10)]


async def test_top_finished_job(aiohttp_server, token):
    async def handler(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        await ws.close()
        return ws

    app = web.Application()
    app.router.add_get("/jobs/job-id/top", handler)

    srv = await aiohttp_server(app)

    lst = []
    async with Client(srv.make_url("/"), token) as client:
        with pytest.raises(ValueError, match="not running"):
            async for data in client.jobs.top("job-id"):
                lst.append(data)
    assert lst == []


async def test_top_nonexisting_job(aiohttp_server, token):
    async def handler(request):
        raise web.HTTPBadRequest()

    app = web.Application()
    app.router.add_get("/jobs/job-id/top", handler)

    srv = await aiohttp_server(app)

    lst = []
    async with Client(srv.make_url("/"), token) as client:
        with pytest.raises(ValueError, match="not found"):
            async for data in client.jobs.top("job-id"):
                lst.append(data)
    assert lst == []


async def test_kill_not_found_error(aiohttp_server, token):
    async def handler(request):
        raise web.HTTPNotFound()

    app = web.Application()
    app.router.add_delete("/jobs/job-id", handler)

    srv = await aiohttp_server(app)

    async with Client(srv.make_url("/"), token) as client:
        with pytest.raises(ResourceNotFound):
            await client.jobs.kill("job-id")


async def test_kill_ok(aiohttp_server, token):
    async def handler(request):
        raise web.HTTPNoContent()

    app = web.Application()
    app.router.add_delete("/jobs/job-id", handler)

    srv = await aiohttp_server(app)

    async with Client(srv.make_url("/"), token) as client:
        ret = await client.jobs.kill("job-id")

    assert ret is None


async def test_status_failed(aiohttp_server, token):
    JSON = {
        "status": "failed",
        "id": "job-id",
        "description": "This is job description, not a history description",
        "http_url": "http://my_host:8889",
        "ssh_server": "ssh://my_host.ssh:22",
        "ssh_auth_server": "ssh://my_host.ssh:22",
        "history": {
            "created_at": "2018-08-29T12:23:13.981621+00:00",
            "started_at": "2018-08-29T12:23:15.988054+00:00",
            "finished_at": "2018-08-29T12:59:31.427795+00:00",
            "reason": "ContainerCannotRun",
            "description": "Not enough coffee",
        },
        "is_preemptible": True,
        "owner": "owner",
        "container": {
            "image": "submit-image-name",
            "command": "submit-command",
            "http": {"port": 8181},
            "ssh": {"port": 22},
            "resources": {
                "memory_mb": "4096",
                "cpu": 7.0,
                "shm": True,
                "gpu": 1,
                "gpu_model": "test-gpu-model",
            },
            "volumes": [
                {
                    "src_storage_uri": "storage://test-user/path_read_only",
                    "dst_path": "/container/read_only",
                    "read_only": True,
                },
                {
                    "src_storage_uri": "storage://test-user/path_read_write",
                    "dst_path": "/container/path_read_write",
                    "read_only": False,
                },
            ],
        },
    }

    async def handler(request):
        return web.json_response(JSON)

    app = web.Application()
    app.router.add_get("/jobs/job-id", handler)

    srv = await aiohttp_server(app)

    async with Client(srv.make_url("/"), token) as client:
        ret = await client.jobs.status("job-id")

    assert ret == JobDescription.from_api(JSON)


async def test_status_with_ssh_and_http(aiohttp_server, token):
    JSON = {
        "status": "running",
        "id": "job-id",
        "description": "This is job description, not a history description",
        "http_url": "http://my_host:8889",
        "ssh_server": "ssh://my_host.ssh:22",
        "ssh_auth_server": "ssh://my_host.ssh:22",
        "history": {
            "created_at": "2018-08-29T12:23:13.981621+00:00",
            "started_at": "2018-08-29T12:23:15.988054+00:00",
            "finished_at": "2018-08-29T12:59:31.427795+00:00",
            "reason": "OK",
            "description": "Everything is fine",
        },
        "is_preemptible": True,
        "owner": "owner",
        "container": {
            "image": "submit-image-name",
            "command": "submit-command",
            "http": {"port": 8181},
            "ssh": {"port": 22},
            "resources": {
                "memory_mb": "4096",
                "cpu": 7.0,
                "shm": True,
                "gpu": 1,
                "gpu_model": "test-gpu-model",
            },
            "volumes": [
                {
                    "src_storage_uri": "storage://test-user/path_read_only",
                    "dst_path": "/container/read_only",
                    "read_only": True,
                },
                {
                    "src_storage_uri": "storage://test-user/path_read_write",
                    "dst_path": "/container/path_read_write",
                    "read_only": False,
                },
            ],
        },
    }

    async def handler(request):
        return web.json_response(JSON)

    app = web.Application()
    app.router.add_get("/jobs/job-id", handler)

    srv = await aiohttp_server(app)

    async with Client(srv.make_url("/"), token) as client:
        ret = await client.jobs.status("job-id")

    assert ret == JobDescription.from_api(JSON)


async def test_job_submit(aiohttp_server, token):
    JSON = {
        "id": "job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
        "status": "failed",
        "history": {
            "status": "failed",
            "reason": "Error",
            "description": "Mounted on Avail\\n/dev/shm     " "64M\\n\\nExit code: 1",
            "created_at": "2018-09-25T12:28:21.298672+00:00",
            "started_at": "2018-09-25T12:28:59.759433+00:00",
            "finished_at": "2018-09-25T12:28:59.759433+00:00",
        },
        "owner": "owner",
        "container": {
            "image": "gcr.io/light-reality-205619/ubuntu:latest",
            "command": "date",
            "resources": {
                "cpu": 1.0,
                "memory_mb": 16384,
                "gpu": 1,
                "shm": False,
                "gpu_model": "nvidia-tesla-p4",
            },
        },
        "http_url": "http://my_host:8889",
        "ssh_server": "ssh://my_host.ssh:22",
        "ssh_auth_server": "ssh://my_host.ssh:22",
        "is_preemptible": False,
    }

    async def handler(request):
        data = await request.json()
        assert data == {
            "container": {
                "image": "submit-image-name",
                "command": "submit-command",
                "http": {"port": 8181, "requires_auth": True},
                "ssh": {"port": 22},
                "resources": {
                    "memory_mb": "4G",
                    "cpu": 7.0,
                    "shm": True,
                    "gpu": 1,
                    "gpu_model": "test-gpu-model",
                },
                "volumes": [
                    {
                        "src_storage_uri": "storage://test-user/path_read_only",
                        "dst_path": "/container/read_only",
                        "read_only": True,
                    },
                    {
                        "src_storage_uri": "storage://test-user/path_read_write",
                        "dst_path": "/container/path_read_write",
                        "read_only": False,
                    },
                ],
            },
            "is_preemptible": False,
            "description": "job description",
        }

        return web.json_response(JSON)

    app = web.Application()
    app.router.add_post("/jobs", handler)

    srv = await aiohttp_server(app)

    async with Client(srv.make_url("/"), token) as client:
        image = Image(image="submit-image-name", command="submit-command")
        network = NetworkPortForwarding({"http": 8181, "ssh": 22})
        resources = Resources.create(7, 1, "test-gpu-model", "4G", True)
        volumes: List[Volume] = [
            Volume("storage://test-user/path_read_only", "/container/read_only", True),
            Volume(
                "storage://test-user/path_read_write",
                "/container/path_read_write",
                False,
            ),
        ]
        ret = await client.jobs.submit(
            image=image,
            resources=resources,
            network=network,
            volumes=volumes,
            is_preemptible=False,
            description="job description",
        )

    assert ret == JobDescription.from_api(JSON)


async def test_job_submit_no_volumes(aiohttp_server, token):
    JSON = {
        "id": "job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
        "status": "failed",
        "history": {
            "status": "failed",
            "reason": "Error",
            "description": "Mounted on Avail\\n/dev/shm     " "64M\\n\\nExit code: 1",
            "created_at": "2018-09-25T12:28:21.298672+00:00",
            "started_at": "2018-09-25T12:28:59.759433+00:00",
            "finished_at": "2018-09-25T12:28:59.759433+00:00",
        },
        "owner": "owner",
        "container": {
            "image": "gcr.io/light-reality-205619/ubuntu:latest",
            "command": "date",
            "resources": {
                "cpu": 1.0,
                "memory_mb": 16384,
                "gpu": 1,
                "shm": False,
                "gpu_model": "nvidia-tesla-p4",
            },
        },
        "http_url": "http://my_host:8889",
        "ssh_server": "ssh://my_host.ssh:22",
        "ssh_auth_server": "ssh://my_host.ssh:22",
        "is_preemptible": False,
    }

    async def handler(request):
        data = await request.json()
        assert data == {
            "container": {
                "image": "submit-image-name",
                "command": "submit-command",
                "http": {"port": 8181, "requires_auth": True},
                "ssh": {"port": 22},
                "resources": {
                    "memory_mb": "4G",
                    "cpu": 7.0,
                    "shm": True,
                    "gpu": 1,
                    "gpu_model": "test-gpu-model",
                },
            },
            "is_preemptible": False,
            "description": "job description",
        }

        return web.json_response(JSON)

    app = web.Application()
    app.router.add_post("/jobs", handler)

    srv = await aiohttp_server(app)

    async with Client(srv.make_url("/"), token) as client:
        image = Image(image="submit-image-name", command="submit-command")
        network = NetworkPortForwarding({"http": 8181, "ssh": 22})
        resources = Resources.create(7, 1, "test-gpu-model", "4G", True)
        ret = await client.jobs.submit(
            image=image,
            resources=resources,
            network=network,
            volumes=None,
            is_preemptible=False,
            description="job description",
        )

    assert ret == JobDescription.from_api(JSON)


async def test_job_submit_preemptible(aiohttp_server, token):
    JSON = {
        "id": "job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
        "status": "failed",
        "history": {
            "status": "failed",
            "reason": "Error",
            "description": "Mounted on Avail\\n/dev/shm     " "64M\\n\\nExit code: 1",
            "created_at": "2018-09-25T12:28:21.298672+00:00",
            "started_at": "2018-09-25T12:28:59.759433+00:00",
            "finished_at": "2018-09-25T12:28:59.759433+00:00",
        },
        "owner": "owner",
        "container": {
            "image": "gcr.io/light-reality-205619/ubuntu:latest",
            "command": "date",
            "resources": {
                "cpu": 1.0,
                "memory_mb": 16384,
                "gpu": 1,
                "shm": False,
                "gpu_model": "nvidia-tesla-p4",
            },
        },
        "is_preemptible": True,
        "http_url": "http://my_host:8889",
        "ssh_server": "ssh://my_host.ssh:22",
        "ssh_auth_server": "ssh://my_host.ssh:22",
    }

    async def handler(request):
        data = await request.json()
        assert data == {
            "container": {
                "image": "submit-image-name",
                "command": "submit-command",
                "http": {"port": 8181, "requires_auth": True},
                "ssh": {"port": 22},
                "resources": {
                    "memory_mb": "4G",
                    "cpu": 7.0,
                    "shm": True,
                    "gpu": 1,
                    "gpu_model": "test-gpu-model",
                },
                "volumes": [
                    {
                        "src_storage_uri": "storage://test-user/path_read_only",
                        "dst_path": "/container/read_only",
                        "read_only": True,
                    },
                    {
                        "src_storage_uri": "storage://test-user/path_read_write",
                        "dst_path": "/container/path_read_write",
                        "read_only": False,
                    },
                ],
            },
            "is_preemptible": True,
            "description": "job description",
        }

        return web.json_response(JSON)

    app = web.Application()
    app.router.add_post("/jobs", handler)

    srv = await aiohttp_server(app)

    async with Client(srv.make_url("/"), token) as client:
        image = Image(image="submit-image-name", command="submit-command")
        network = NetworkPortForwarding({"http": 8181, "ssh": 22})
        resources = Resources.create(7, 1, "test-gpu-model", "4G", True)
        volumes: List[Volume] = [
            Volume("storage://test-user/path_read_only", "/container/read_only", True),
            Volume(
                "storage://test-user/path_read_write",
                "/container/path_read_write",
                False,
            ),
        ]
        ret = await client.jobs.submit(
            image=image,
            resources=resources,
            network=network,
            volumes=volumes,
            is_preemptible=True,
            description="job description",
        )

    assert ret == JobDescription.from_api(JSON)


@pytest.mark.parametrize(
    "volume",
    [("storage:///"), (":"), ("::::"), (""), ("storage:///data/:/data/rest:wrong")],
)
def test_volume_from_str_fail(volume):
    with pytest.raises(ValueError):
        Volume.from_cli("testuser", volume)


async def test_list(aiohttp_server, token):
    JSON = {
        "jobs": [
            {
                "id": "job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
                "status": "pending",
                "history": {
                    "status": "failed",
                    "reason": "Error",
                    "description": "Mounted on Avail\\n/dev/shm     "
                    "64M\\n\\nExit code: 1",
                    "created_at": "2018-09-25T12:28:21.298672+00:00",
                    "started_at": "2018-09-25T12:28:59.759433+00:00",
                    "finished_at": "2018-09-25T12:28:59.759433+00:00",
                },
                "ssh_auth_server": "ssh://my_host.ssh:22",
                "container": {
                    "image": "submit-image-name",
                    "command": "submit-command",
                    "resources": {
                        "cpu": 1.0,
                        "memory_mb": 16384,
                        "gpu": 1,
                        "gpu_model": "nvidia-tesla-v100",
                    },
                },
                "is_preemptible": True,
                "owner": "owner",
            }
        ]
    }

    async def handler(request):
        return web.json_response(JSON)

    app = web.Application()
    app.router.add_get("/jobs", handler)

    srv = await aiohttp_server(app)
    statuses = {"pending", "running", "failed", "succeeded"}

    async with Client(srv.make_url("/"), token) as client:
        ret = await client.jobs.list(statuses)

    assert ret == [JobDescription.from_api(j) for j in JSON["jobs"]]


class TestVolumeParsing:
    @pytest.mark.parametrize(
        "volume_param", ["dir", "storage://dir", "storage://dir:/var/www:rw:ro"]
    )
    def test_incorrect_params_count(self, volume_param):
        with pytest.raises(ValueError, match=r"Invalid volume specification"):
            Volume.from_cli("bob", volume_param)

    @pytest.mark.parametrize(
        "volume_param", ["storage://dir:/var/www:write", "storage://dir:/var/www:"]
    )
    def test_incorrect_mode(self, volume_param):
        with pytest.raises(ValueError, match=r"Wrong ReadWrite/ReadOnly mode spec"):
            Volume.from_cli("bob", volume_param)

    @pytest.mark.parametrize(
        "volume_param,volume",
        [
            (
                "storage://bob/dir:/var/www",
                Volume(
                    storage_path="storage://bob/dir",
                    container_path="/var/www",
                    read_only=False,
                ),
            ),
            (
                "storage://bob/dir:/var/www:rw",
                Volume(
                    storage_path="storage://bob/dir",
                    container_path="/var/www",
                    read_only=False,
                ),
            ),
            (
                "storage://bob:/var/www:ro",
                Volume(
                    storage_path="storage://bob",
                    container_path="/var/www",
                    read_only=True,
                ),
            ),
            (
                "storage://~/:/var/www:ro",
                Volume(
                    storage_path="storage://bob",
                    container_path="/var/www",
                    read_only=True,
                ),
            ),
            (
                    "storage:dir:/var/www:ro",
                    Volume(
                        storage_path="storage://bob/dir",
                        container_path="/var/www",
                        read_only=True,
                    ),
            ),
            (
                    "storage::/var/www:ro",
                    Volume(
                        storage_path="storage://bob",
                        container_path="/var/www",
                        read_only=True,
                    ),
            ),
        ],
    )
    def test_positive(self, volume_param, volume):
        assert Volume.from_cli("bob", volume_param) == volume
