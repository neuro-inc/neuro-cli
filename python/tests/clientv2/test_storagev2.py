import pytest
from aiohttp import web
from yarl import URL

from neuromation.clientv2 import ClientV2, FileStatus


async def test_uri_to_path_non_storage():
    async with ClientV2(URL("https://example.com"), "user", "token") as client:
        with pytest.raises(ValueError):
            client.storage._uri_to_path(URL("bad-schema://something"))


async def test_uri_to_path_home():
    async with ClientV2(URL("https://example.com"), "user", "token") as client:
        assert client.storage._uri_to_path(URL("storage://~/path")) == "user/path"


async def test_uri_to_path_no_user():
    async with ClientV2(URL("https://example.com"), "user", "token") as client:
        assert client.storage._uri_to_path(URL("storage:/data")) == "user/data"


async def test_uri_to_path_explicit_user():
    async with ClientV2(URL("https://example.com"), "user", "token") as client:
        assert client.storage._uri_to_path(URL("storage://alice/data")) == "alice/data"


async def test_uri_to_path_to_file():
    async with ClientV2(URL("https://example.com"), "user", "token") as client:
        assert (
            client.storage._uri_to_path(URL("storage://alice/data/foo.txt"))
            == "alice/data/foo.txt"
        )


async def test_uri_to_path_strip_slash():
    async with ClientV2(URL("https://example.com"), "user", "token") as client:
        assert (
            client.storage._uri_to_path(URL("storage://alice/data/foo.txt/"))
            == "alice/data/foo.txt"
        )


async def test_uri_to_path_root():
    async with ClientV2(URL("https://example.com"), "user", "token") as client:
        assert client.storage._uri_to_path(URL("storage:")) == "user"


async def test_uri_to_path_root2():
    async with ClientV2(URL("https://example.com"), "user", "token") as client:
        assert client.storage._uri_to_path(URL("storage:/")) == "user"


async def test_uri_to_path_root3():
    async with ClientV2(URL("https://example.com"), "user", "token") as client:
        assert client.storage._uri_to_path(URL("storage://")) == "user"


@pytest.mark.xfail
async def test_uri_to_path_root4():
    async with ClientV2(URL("https://example.com"), "user", "token") as client:
        assert client.storage._uri_to_path(URL("storage:///")) == "/"


async def test_uri_to_path_relative():
    async with ClientV2(URL("https://example.com"), "user", "token") as client:
        assert client.storage._uri_to_path(URL("storage:path")) == "user/path"


async def test_storage_ls(aiohttp_server):
    JSON = {
        "FileStatuses": {
            "FileStatus": [
                {
                    "path": "foo",
                    "length": 1024,
                    "type": "FILE",
                    "modificationTime": 0,
                    "permission": "read",
                },
                {
                    "path": "bar",
                    "length": 4 * 1024,
                    "type": "DIR",
                    "modificationTime": 0,
                    "permission": "read",
                },
            ]
        }
    }

    async def handler(request):
        assert request.path == "/storage/user/folder"
        assert request.query == {"op": "LISTSTATUS"}
        return web.json_response(JSON)

    app = web.Application()
    app.router.add_get("/storage/user/folder", handler)

    srv = await aiohttp_server(app)

    async with ClientV2(srv.make_url("/"), "user", "token") as client:
        ret = await client.storage.ls(URL("storage://~/folder"))

    assert ret == [
        FileStatus(
            path="foo", size=1024, type="FILE", modification_time=0, permission="read"
        ),
        FileStatus(
            path="bar",
            size=4 * 1024,
            type="DIR",
            modification_time=0,
            permission="read",
        ),
    ]


async def test_storage_rm(aiohttp_server):
    async def handler(request):
        assert request.path == "/storage/user/folder"
        assert request.query == {"op": "DELETE"}
        return web.Response(status=204)

    app = web.Application()
    app.router.add_delete("/storage/user/folder", handler)

    srv = await aiohttp_server(app)

    async with ClientV2(srv.make_url("/"), "user", "token") as client:
        await client.storage.rm(URL("storage://~/folder"))


async def test_storage_mv(aiohttp_server):
    async def handler(request):
        assert request.path == "/storage/user/folder"
        assert request.query == {"op": "RENAME", "destination": "/user/other"}
        return web.Response(status=204)

    app = web.Application()
    app.router.add_post("/storage/user/folder", handler)

    srv = await aiohttp_server(app)

    async with ClientV2(srv.make_url("/"), "user", "token") as client:
        await client.storage.mv(URL("storage://~/folder"), URL("storage://~/other"))


async def test_storage_mkdir(aiohttp_server):
    async def handler(request):
        assert request.path == "/storage/user/folder"
        assert request.query == {"op": "MKDIRS"}
        return web.Response(status=204)

    app = web.Application()
    app.router.add_put("/storage/user/folder", handler)

    srv = await aiohttp_server(app)

    async with ClientV2(srv.make_url("/"), "user", "token") as client:
        await client.storage.mkdirs(URL("storage://~/folder"))
