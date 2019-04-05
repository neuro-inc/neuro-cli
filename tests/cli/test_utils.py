import pytest
from aiohttp import web
from yarl import URL

from neuromation.cli.utils import (
    parse_permission_action,
    parse_resource_for_sharing,
    resolve_job,
)
from neuromation.client import Action, Client


async def test_resolve_job_id__no_jobs_found(aiohttp_server, token):
    JSON = {"jobs": []}
    job_id = "job-81839be3-3ecf-4ec5-80d9-19b1588869db"
    job_name_to_resolve = job_id

    async def handler(request):
        assert request.query.get("name") == job_name_to_resolve
        return web.json_response(JSON)

    app = web.Application()
    app.router.add_get("/jobs", handler)

    srv = await aiohttp_server(app)

    async with Client(srv.make_url("/"), token) as client:
        resolved = await resolve_job(client, job_name_to_resolve)
        assert resolved == job_id


async def test_resolve_job_id__single_job_found(aiohttp_server, token):
    job_name_to_resolve = "test-job-name-555"
    JSON = {
        "jobs": [
            {
                "id": "job-efb7d723-722c-4d5c-a5db-de258db4b09e",
                "owner": "test1",
                "status": "running",
                "history": {
                    "status": "running",
                    "reason": None,
                    "description": None,
                    "created_at": "2019-03-18T12:41:10.573468+00:00",
                    "started_at": "2019-03-18T12:41:16.804040+00:00",
                },
                "container": {
                    "image": "ubuntu:latest",
                    "env": {},
                    "volumes": [],
                    "command": "sleep 1h",
                    "resources": {"cpu": 0.1, "memory_mb": 1024, "shm": True},
                },
                "ssh_auth_server": "ssh://nobody@ssh-auth-dev.neu.ro:22",
                "is_preemptible": True,
                "name": job_name_to_resolve,
                "internal_hostname": "job-efb7d723-722c-4d5c-a5db-de258db4b09e.default",
            }
        ]
    }
    job_id = JSON["jobs"][0]["id"]

    async def handler(request):
        assert request.query.get("name") == job_name_to_resolve
        return web.json_response(JSON)

    app = web.Application()
    app.router.add_get("/jobs", handler)

    srv = await aiohttp_server(app)

    async with Client(srv.make_url("/"), token) as client:
        resolved = await resolve_job(client, job_name_to_resolve)
        assert resolved == job_id


async def test_resolve_job_id__multiple_jobs_found(aiohttp_server, token):
    job_name_to_resolve = "job-name-123-000"
    JSON = {
        "jobs": [
            {
                "id": "job-d912aa8c-d01b-44bd-b77c-5a19fc151f89",
                "owner": "test1",
                "status": "succeeded",
                "history": {
                    "status": "succeeded",
                    "reason": None,
                    "description": None,
                    "created_at": "2019-03-17T16:24:54.746175+00:00",
                    "started_at": "2019-03-17T16:25:00.868880+00:00",
                    "finished_at": "2019-03-17T16:28:01.298487+00:00",
                },
                "container": {
                    "image": "ubuntu:latest",
                    "env": {},
                    "volumes": [],
                    "command": "sleep 3m",
                    "resources": {"cpu": 0.1, "memory_mb": 1024, "shm": True},
                },
                "ssh_auth_server": "ssh://nobody@ssh-auth-dev.neu.ro:22",
                "is_preemptible": True,
                "name": job_name_to_resolve,
                "internal_hostname": "job-d912aa8c-d01b-44bd-b77c-5a19fc151f89.default",
            },
            {
                "id": "job-e5071b6b-2e97-4cce-b12d-86e31751dc8a",
                "owner": "test1",
                "status": "succeeded",
                "history": {
                    "status": "succeeded",
                    "reason": None,
                    "description": None,
                    "created_at": "2019-03-18T11:31:03.669549+00:00",
                    "started_at": "2019-03-18T11:31:10.428975+00:00",
                    "finished_at": "2019-03-18T11:31:54.896666+00:00",
                },
                "container": {
                    "image": "ubuntu:latest",
                    "env": {},
                    "volumes": [],
                    "command": "sleep 5m",
                    "resources": {"cpu": 0.1, "memory_mb": 1024, "shm": True},
                },
                "ssh_auth_server": "ssh://nobody@ssh-auth-dev.neu.ro:22",
                "is_preemptible": True,
                "name": job_name_to_resolve,
                "internal_hostname": "job-e5071b6b-2e97-4cce-b12d-86e31751dc8a.default",
            },
        ]
    }
    job_id = JSON["jobs"][-1]["id"]

    async def handler(request):
        assert request.query.get("name") == job_name_to_resolve
        return web.json_response(JSON)

    app = web.Application()
    app.router.add_get("/jobs", handler)

    srv = await aiohttp_server(app)

    async with Client(srv.make_url("/"), token) as client:
        resolved = await resolve_job(client, job_name_to_resolve)
        assert resolved == job_id


async def test_resolve_job_id__server_error(aiohttp_server, token):
    job_id = "job-81839be3-3ecf-4ec5-80d9-19b1588869db"
    job_name_to_resolve = job_id

    async def handler(request):
        assert request.query.get("name") == job_name_to_resolve
        raise web.HTTPError()

    app = web.Application()
    app.router.add_get("/jobs", handler)

    srv = await aiohttp_server(app)

    async with Client(srv.make_url("/"), token) as client:
        resolved = await resolve_job(client, job_name_to_resolve)
        assert resolved == job_id


def test_parse_resource_for_sharing_image_no_tag(config):
    uri = "image://~/ubuntu"
    parsed = parse_resource_for_sharing(uri, config)
    assert parsed == URL("image://user/ubuntu:latest")


def test_parse_resource_for_sharing_image_with_tag_fail(config):
    uri = "image://~/ubuntu:latest"
    with pytest.raises(ValueError, match="tag is not allowed"):
        parse_resource_for_sharing(uri, config)


def test_parse_permission_action_read_lowercase(config):
    action = "read"
    assert parse_permission_action(action) == Action.READ


def test_parse_permission_action_read(config):
    action = "READ"
    assert parse_permission_action(action) == Action.READ


def test_parse_permission_action_write_lowercase(config):
    action = "write"
    assert parse_permission_action(action) == Action.WRITE


def test_parse_permission_action_write(config):
    action = "WRITE"
    assert parse_permission_action(action) == Action.WRITE


def test_parse_permission_action_manage_lowercase(config):
    action = "manage"
    assert parse_permission_action(action) == Action.MANAGE


def test_parse_permission_action_manage(config):
    action = "MANAGE"
    assert parse_permission_action(action) == Action.MANAGE


def test_parse_permission_action_wrong_string(config):
    action = "tosh"
    err = "invalid permission action 'tosh', allowed values: read, write, manage"
    with pytest.raises(ValueError, match=err):
        parse_permission_action(action)


def test_parse_permission_action_wrong_empty(config):
    action = ""
    err = "invalid permission action '', allowed values: read, write, manage"
    with pytest.raises(ValueError, match=err):
        parse_permission_action(action)
