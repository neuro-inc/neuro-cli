import pytest
from aiohttp import web
from yarl import URL

from neuromation.client import ResourceNotFound
from neuromation.clientv2 import ClientV2, JobDescription, JobStatus, JobStatusHistory


async def test_jobs_monitor(aiohttp_server):
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
    async with ClientV2(srv.make_url("/"), "token") as client:
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


async def test_monitor_notexistent_job(aiohttp_server):
    async def handler(request):
        raise web.HTTPNotFound()

    app = web.Application()
    app.router.add_get("/jobs/job-id/log", handler)

    srv = await aiohttp_server(app)

    lst = []
    async with ClientV2(srv.make_url("/"), "token") as client:
        with pytest.raises(ResourceNotFound):
            async for data in client.jobs.monitor("job-id"):
                lst.append(data)
    assert lst == []


async def test_kill_not_found_error(aiohttp_server):
    async def handler(request):
        raise web.HTTPNotFound()

    app = web.Application()
    app.router.add_delete("/jobs/job-id", handler)

    srv = await aiohttp_server(app)

    async with ClientV2(srv.make_url("/"), "token") as client:
        with pytest.raises(ResourceNotFound):
            await client.jobs.kill("job-id")


async def test_kill(aiohttp_server):
    async def handler(request):
        raise web.HTTPNoContent()

    app = web.Application()
    app.router.add_delete("/jobs/job-id", handler)

    srv = await aiohttp_server(app)

    async with ClientV2(srv.make_url("/"), "token") as client:
        ret = await client.jobs.kill("job-id")

    assert ret is None


async def test_status_failed(aiohttp_server):
    async def handler(request):
        return web.json_response(
            {
                "status": "failed",
                "id": "job-id",
                "description": "This is job description, not a history description",
                "history": {
                    "created_at": "2018-08-29T12:23:13.981621+00:00",
                    "started_at": "2018-08-29T12:23:15.988054+00:00",
                    "finished_at": "2018-08-29T12:59:31.427795+00:00",
                    "reason": "ContainerCannotRun",
                    "description": "Not enough coffee",
                },
            }
        )

    app = web.Application()
    app.router.add_get("/jobs/job-id", handler)

    srv = await aiohttp_server(app)

    async with ClientV2(srv.make_url("/"), "token") as client:
        ret = await client.jobs.status("job-id")

    assert ret == JobDescription(
        id="job-id",
        status=JobStatus.FAILED,
        description="This is job description, not a history description",
        history=JobStatusHistory(
            created_at="2018-08-29T12:23:13.981621+00:00",
            started_at="2018-08-29T12:23:15.988054+00:00",
            finished_at="2018-08-29T12:59:31.427795+00:00",
            status=JobStatus.UNKNOWN,
            reason="ContainerCannotRun",
            description="Not enough coffee",
        ),
    )


async def test_status_with_ssh_and_http(aiohttp_server):
    async def handler(request):
        return web.json_response(
            {
                "status": "running",
                "id": "job-id",
                "description": "This is job description, not a history description",
                "http_url": "http://my_host:8889",
                "ssh_server": "ssh://my_host.ssh:22",
                "history": {
                    "created_at": "2018-08-29T12:23:13.981621+00:00",
                    "started_at": "2018-08-29T12:23:15.988054+00:00",
                    "finished_at": "2018-08-29T12:59:31.427795+00:00",
                    "reason": "OK",
                    "description": "Everything is fine",
                },
            }
        )

    app = web.Application()
    app.router.add_get("/jobs/job-id", handler)

    srv = await aiohttp_server(app)

    async with ClientV2(srv.make_url("/"), "token") as client:
        ret = await client.jobs.status("job-id")

    assert ret == JobDescription(
        id="job-id",
        status=JobStatus.RUNNING,
        description="This is job description, not a history description",
        history=JobStatusHistory(
            created_at="2018-08-29T12:23:13.981621+00:00",
            started_at="2018-08-29T12:23:15.988054+00:00",
            finished_at="2018-08-29T12:59:31.427795+00:00",
            status=JobStatus.UNKNOWN,
            reason="OK",
            description="Everything is fine",
        ),
        url=URL("http://my_host:8889"),
        ssh=URL("ssh://my_host.ssh:22"),
    )
