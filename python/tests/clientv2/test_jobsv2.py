import pytest
from aiohttp import web

from neuromation.client import ResourceNotFound
from neuromation.clientv2 import ClientV2


async def test_jobs_monitor(aiohttp_server):
    async def log_stream(request):
        assert request.headers['Accept-Encoding'] == 'identity'
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
    client = ClientV2(srv.make_url("/"), "token")
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
    app = web.Application()

    srv = await aiohttp_server(app)

    lst = []
    client = ClientV2(srv.make_url("/"), "token")
    with pytest.raises(ResourceNotFound):
        async for data in client.jobs.monitor("job-id"):
            lst.append(data)
    assert lst == []
