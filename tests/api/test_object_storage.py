import base64
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict  # noqa: F401

from aiohttp import web

from neuromation.api import Action, BucketListing, Client, ObjectListing, PrefixListing
from neuromation.api.object_storage import calc_md5
from tests import _TestServerFactory


_MakeClient = Callable[..., Client]


FOLDER = Path(__file__).parent
DATA_FOLDER = FOLDER / "data"


class OBSUrlRotes:

    LIST_BUCKETS = r"/obs/b/"
    PUT_BUCKET = r"/obs/b/{bucket}"
    DELETE_BUCKET = r"/obs/b/{bucket}"

    LIST_OBJECTS = r"/obs/o/{bucket}"
    HEAD_OBJECT = r"/obs/o/{bucket}/{path:.+}"
    GET_OBJECT = r"/obs/o/{bucket}/{path:.+}"
    PUT_OBJECT = r"/obs/o/{bucket}/{path:.+}"


# Bucket `foo` structure
# foo
# ├── empty/
# ├── folder1/
# │   ├── xxx.txt
# │   └── yyy.json
# ├── folder2/
# │   └── big_file
# ├── test.json
# ├── test1.txt
# └── test2.txt


async def test_object_storage_list_buckets(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    mtime1 = datetime.now()
    mtime2 = datetime.now()
    JSON = [
        {"name": "foo", "creation_date": mtime1.isoformat()},
        {"name": "bar", "creation_date": mtime2.isoformat()},
    ]

    async def handler(request: web.Request) -> web.Response:
        assert "b3" in request.headers
        assert request.path == OBSUrlRotes.LIST_BUCKETS
        assert request.query == {}
        return web.json_response(JSON)

    app = web.Application()
    app.router.add_get(OBSUrlRotes.LIST_BUCKETS, handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        ret = await client.object_storage.list_buckets()

    assert ret == [
        BucketListing(
            name="foo",
            modification_time=int(mtime1.timestamp()),
            permission=Action.READ,
        ),
        BucketListing(
            name="bar",
            modification_time=int(mtime2.timestamp()),
            permission=Action.READ,
        ),
    ]


async def test_object_storage_list_objects(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    bucket_name = "foo"
    mtime1 = datetime.now()
    mtime2 = datetime.now()
    PAGE1_JSON = {
        "contents": [
            {"key": "test.json", "size": 213, "last_modified": mtime1.timestamp()}
        ],
        "common_prefixes": [{"prefix": "empty/"}, {"prefix": "folder1/"}],
        "is_truncated": True,
    }
    PAGE2_JSON = {
        "contents": [
            {"key": "test1.txt", "size": 111, "last_modified": mtime1.timestamp()},
            {"key": "test2.txt", "size": 222, "last_modified": mtime2.timestamp()},
        ],
        "common_prefixes": [{"prefix": "folder2/"}],
        "is_truncated": False,
    }

    async def handler(request: web.Request) -> web.Response:
        assert "b3" in request.headers
        assert request.path == OBSUrlRotes.LIST_OBJECTS.format(bucket=bucket_name)

        if "start_after" not in request.query:
            assert request.query == {"recursive": "false", "max_keys": "3"}
            return web.json_response(PAGE1_JSON)
        else:
            assert request.query == {
                "recursive": "false",
                "max_keys": "3",
                "start_after": "test.json",
            }
            return web.json_response(PAGE2_JSON)

    app = web.Application()
    app.router.add_get(OBSUrlRotes.LIST_OBJECTS, handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        client.object_storage._max_keys = 3
        ret = await client.object_storage.list_objects(bucket_name)

    assert ret == [
        PrefixListing(prefix="empty/", bucket_name=bucket_name),
        PrefixListing(prefix="folder1/", bucket_name=bucket_name),
        PrefixListing(prefix="folder2/", bucket_name=bucket_name),
        ObjectListing(
            key="test.json",
            size=213,
            modification_time=int(mtime1.timestamp()),
            bucket_name=bucket_name,
        ),
        ObjectListing(
            key="test1.txt",
            size=111,
            modification_time=int(mtime1.timestamp()),
            bucket_name=bucket_name,
        ),
        ObjectListing(
            key="test2.txt",
            size=222,
            modification_time=int(mtime2.timestamp()),
            bucket_name=bucket_name,
        ),
    ]


async def test_object_storage_list_objects_recursive(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    bucket_name = "foo"
    mtime1 = datetime.now()
    mtime2 = datetime.now()
    PAGE1_JSON = {
        "contents": [
            {"key": "folder1/xxx.txt", "size": 1, "last_modified": mtime1.timestamp()},
            {"key": "folder1/yyy.json", "size": 2, "last_modified": mtime2.timestamp()},
            {
                "key": "folder2/big_file",
                "size": 120 * 1024 * 1024,
                "last_modified": mtime1.timestamp(),
            },
        ],
        "common_prefixes": [],
        "is_truncated": False,
    }

    async def handler(request: web.Request) -> web.Response:
        assert "b3" in request.headers
        assert request.path == OBSUrlRotes.LIST_OBJECTS.format(bucket=bucket_name)
        assert request.query == {
            "recursive": "true",
            "max_keys": "10000",
            "prefix": "folder",
        }
        return web.json_response(PAGE1_JSON)

    app = web.Application()
    app.router.add_get(OBSUrlRotes.LIST_OBJECTS, handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        ret = await client.object_storage.list_objects(
            bucket_name, recursive=True, prefix="folder"
        )

    assert ret == [
        ObjectListing(
            key="folder1/xxx.txt",
            size=1,
            modification_time=int(mtime1.timestamp()),
            bucket_name=bucket_name,
        ),
        ObjectListing(
            key="folder1/yyy.json",
            size=2,
            modification_time=int(mtime2.timestamp()),
            bucket_name=bucket_name,
        ),
        ObjectListing(
            key="folder2/big_file",
            size=120 * 1024 * 1024,
            modification_time=int(mtime1.timestamp()),
            bucket_name=bucket_name,
        ),
    ]


async def test_object_storage_glob_objects(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    bucket_name = "foo"
    mtime1 = datetime.now()
    mtime2 = datetime.now()
    PAGE1_JSON: Dict[str, Any] = {
        "contents": [
            {"key": "folder1/xxx.txt", "size": 1, "last_modified": mtime1.timestamp()},
            {"key": "folder1/yyy.json", "size": 2, "last_modified": mtime2.timestamp()},
            {
                "key": "folder2/big_file",
                "size": 120 * 1024 * 1024,
                "last_modified": mtime1.timestamp(),
            },
            {"key": "test.json", "size": 213, "last_modified": mtime1.timestamp()},
            {"key": "test1.txt", "size": 111, "last_modified": mtime1.timestamp()},
            {"key": "test2.txt", "size": 222, "last_modified": mtime2.timestamp()},
        ],
        "common_prefixes": [],
        "is_truncated": False,
    }

    async def handler(request: web.Request) -> web.Response:
        assert "b3" in request.headers
        assert request.path == OBSUrlRotes.LIST_OBJECTS.format(bucket=bucket_name)
        expected = {
            "recursive": "true",
            "max_keys": "10000",
        }
        prefix = ""
        if "prefix" in request.query:
            expected["prefix"] = prefix = request.query["prefix"]
        assert request.query == expected
        # Filter by prefix
        contents = []
        for ob in PAGE1_JSON["contents"]:
            if ob["key"].startswith(prefix):
                contents.append(ob)
        resp = PAGE1_JSON.copy()
        resp["contents"] = contents
        return web.json_response(resp)

    app = web.Application()
    app.router.add_get(OBSUrlRotes.LIST_OBJECTS, handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        ret = await client.object_storage.glob_objects(bucket_name, pattern="folder1/*")

        assert ret == [
            ObjectListing(
                key="folder1/xxx.txt",
                size=1,
                modification_time=int(mtime1.timestamp()),
                bucket_name=bucket_name,
            ),
            ObjectListing(
                key="folder1/yyy.json",
                size=2,
                modification_time=int(mtime2.timestamp()),
                bucket_name=bucket_name,
            ),
        ]

        ret = await client.object_storage.glob_objects(bucket_name, pattern="**.json")

        assert ret == [
            ObjectListing(
                key="folder1/yyy.json",
                size=2,
                modification_time=int(mtime2.timestamp()),
                bucket_name=bucket_name,
            ),
            ObjectListing(
                key="test.json",
                size=213,
                modification_time=int(mtime1.timestamp()),
                bucket_name="foo",
            ),
        ]

        ret = await client.object_storage.glob_objects(bucket_name, pattern="*/*.txt")

        assert ret == [
            ObjectListing(
                key="folder1/xxx.txt",
                size=1,
                modification_time=int(mtime1.timestamp()),
                bucket_name=bucket_name,
            )
        ]

        ret = await client.object_storage.glob_objects(
            bucket_name, pattern="test[1-9].*"
        )

        assert ret == [
            ObjectListing(
                key="test1.txt",
                size=111,
                modification_time=int(mtime1.timestamp()),
                bucket_name="foo",
            ),
            ObjectListing(
                key="test2.txt",
                size=222,
                modification_time=int(mtime2.timestamp()),
                bucket_name="foo",
            ),
        ]


async def test_object_storage_head_object(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    bucket_name = "foo"
    key = "text.txt"
    mtime1 = datetime.now()

    async def handler(request: web.Request) -> web.StreamResponse:
        assert "b3" in request.headers
        assert request.path == f"/obs/o/{bucket_name}/{key}"
        assert request.match_info == {"bucket": bucket_name, "path": key}
        resp = web.StreamResponse(status=200)
        resp.headers.update({"ETag": '"12312908asd"'})
        resp.last_modified = mtime1
        resp.content_length = 111
        resp.content_type = "plain/text"
        return resp

    app = web.Application()
    app.router.add_head(OBSUrlRotes.HEAD_OBJECT, handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        ret = await client.object_storage.head_object(bucket_name, key=key)

    assert ret == ObjectListing(
        key=key,
        size=111,
        modification_time=int(mtime1.timestamp()),
        bucket_name=bucket_name,
    )


async def test_object_storage_get_object(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    bucket_name = "foo"
    key = "text.txt"
    mtime1 = datetime.now()
    body = b"W" * 1000

    async def handler(request: web.Request) -> web.StreamResponse:
        assert "b3" in request.headers
        assert request.path == f"/obs/o/{bucket_name}/{key}"
        assert request.match_info == {"bucket": bucket_name, "path": key}
        resp = web.StreamResponse(status=200)
        resp.headers.update({"ETag": '"12312908asd"'})
        resp.last_modified = mtime1
        resp.content_length = len(body)
        resp.content_type = "plain/text"
        await resp.prepare(request)
        await resp.write(body)
        return resp

    app = web.Application()
    app.router.add_get(OBSUrlRotes.GET_OBJECT, handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        async with client.object_storage.get_object(bucket_name, key=key) as ret:
            assert ret.stats == ObjectListing(
                key=key,
                size=1000,
                modification_time=int(mtime1.timestamp()),
                bucket_name=bucket_name,
            )
            assert await ret.body_stream.read() == body


async def test_object_storage_fetch_object(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    bucket_name = "foo"
    key = "text.txt"
    mtime1 = datetime.now()
    body = b"W" * 10 * 1024 * 1024

    async def handler(request: web.Request) -> web.StreamResponse:
        assert "b3" in request.headers
        assert request.path == f"/obs/o/{bucket_name}/{key}"
        assert request.match_info == {"bucket": bucket_name, "path": key}
        resp = web.StreamResponse(status=200)
        resp.headers.update({"ETag": '"12312908asd"'})
        resp.last_modified = mtime1
        resp.content_length = len(body)
        resp.content_type = "plain/text"
        await resp.prepare(request)
        await resp.write(body)
        return resp

    app = web.Application()
    app.router.add_get(OBSUrlRotes.GET_OBJECT, handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        buf = b""
        async for data in client.object_storage.fetch_object(bucket_name, key=key):
            buf += data
        assert buf == body


async def test_object_storage_put_object(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    bucket_name = "foo"
    key = "text.txt"
    body = b"W" * 10 * 1024 * 1024
    md5 = base64.b64encode(hashlib.md5(body).digest()).decode()
    etag = repr(hashlib.md5(body).hexdigest())

    async def handler(request: web.Request) -> web.StreamResponse:
        assert "b3" in request.headers
        assert request.path == f"/obs/o/{bucket_name}/{key}"
        assert request.match_info == {"bucket": bucket_name, "path": key}
        assert request.headers["X-Content-Length"] == str(len(body))
        assert await request.content.read() == body
        return web.Response(headers={"ETag": etag})

    app = web.Application()
    app.router.add_put(OBSUrlRotes.PUT_OBJECT, handler)

    srv = await aiohttp_server(app)

    async def async_iter() -> AsyncIterator[bytes]:
        yield body

    async with make_client(srv.make_url("/")) as client:
        resp_etag = await client.object_storage.put_object(
            bucket_name=bucket_name,
            key=key,
            body_stream=async_iter(),
            size=len(body),
            content_md5=md5,
        )
        assert resp_etag == etag


async def test_object_storage_calc_md5(tmp_path: Path) -> None:
    txt_file = tmp_path / "test.txt"
    body = b"""
    This is the greatest day of my whole life!!!
    """
    body_md5 = base64.b64encode(hashlib.md5(body).digest()).decode("ascii")
    with txt_file.open("wb") as f:
        f.write(body)
    assert await calc_md5(txt_file) == body_md5


async def test_object_storage_large_calc_md5(tmp_path: Path) -> None:
    txt_file = tmp_path / "test.txt"
    size_mb = 20
    body = b"W" * (1024 * 1024)
    md5 = hashlib.md5()
    for _ in range(size_mb):
        md5.update(body)
    body_md5 = base64.b64encode(md5.digest()).decode("ascii")

    # Will write 100MB file
    with txt_file.open("wb") as f:
        for _ in range(size_mb):
            f.write(body)
    assert await calc_md5(txt_file) == body_md5
