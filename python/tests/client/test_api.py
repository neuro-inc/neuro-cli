import pytest
from aiohttp import web

from neuromation.cli.rc import Client
from neuromation.client import IllegalArgumentError


async def test_api_request_error_has_message(aiohttp_server, token):
    ERROR_MSG = '{"error": "this is the error message"}'

    async def handler(request):
        raise web.HTTPBadRequest(text=ERROR_MSG)

    app = web.Application()
    app.router.add_get("/jobs/job-id", handler)
    srv = await aiohttp_server(app)

    async with Client(srv.make_url("/"), token) as client:
        with pytest.raises(IllegalArgumentError, match=ERROR_MSG):
            await client.jobs.status("job-id")
