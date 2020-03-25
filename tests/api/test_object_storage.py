import base64
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Set  # noqa: F401
from unittest import mock

import pytest
from aiohttp import web
from yarl import URL

from neuromation.api import (
    Action,
    BucketListing,
    Client,
    ObjectListing,
    PrefixListing,
    StorageProgressComplete,
    StorageProgressStart,
    StorageProgressStep,
)
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


_ContentsObj = Dict[str, Dict[str, Any]]


def dir_list(path: Path) -> List[Dict[str, Any]]:
    # List all files and folders in directory
    res = []
    for item in path.glob("**/*"):
        if item.is_dir():
            res.append({"path": str(item.relative_to(path)), "dir": True})
        else:
            res.append(
                {
                    "path": str(item.relative_to(path)),
                    "dir": False,
                    "size": item.stat().st_size,
                    "body": item.read_bytes().replace(b"\n\r", b"\n"),  # Fix Windows
                }
            )
    return res


@pytest.fixture
def object_storage_contents() -> _ContentsObj:
    mtime1 = datetime(2019, 1, 1)
    mtime2 = datetime(2019, 1, 2)

    contents: Dict[str, Dict[str, Any]] = {
        "empty/": {
            "key": "empty/",
            "size": 0,
            "last_modified": mtime1.timestamp(),
            "body": b"",
        },
        "folder1/xxx.txt": {
            "key": "folder1/xxx.txt",
            "size": 1,
            "last_modified": mtime1.timestamp(),
            "body": b"w",
        },
        "folder1/yyy.json": {
            "key": "folder1/yyy.json",
            "size": 2,
            "last_modified": mtime2.timestamp(),
            "body": b"bb",
        },
        "test.json": {
            "key": "test.json",
            "size": 213,
            "last_modified": mtime1.timestamp(),
            "body": b"w" * 213,
        },
        "test1.txt": {
            "key": "test1.txt",
            "size": 111,
            "last_modified": mtime1.timestamp(),
            "body": b"w" * 111,
        },
        "test2.txt": {
            "key": "test2.txt",
            "size": 222,
            "last_modified": mtime2.timestamp(),
            "body": b"w" * 222,
        },
    }
    return contents


@pytest.fixture
async def object_storage_server(
    aiohttp_server: _TestServerFactory, object_storage_contents: _ContentsObj,
) -> Any:
    """ Minimal functional Object Storage server implementation
    """
    CONTENTS = object_storage_contents

    def with_keys(d: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
        res = {}
        for k, v in d.items():
            if k in keys:
                res[k] = v
        return res

    LIST_KEYS = ["key", "size", "last_modified"]

    app = web.Application()
    # fill route table

    async def list_buckets(request: web.Request) -> web.Response:
        assert "b3" in request.headers
        return web.json_response(
            [{"name": "foo", "creation_date": datetime(2019, 1, 1).isoformat()}]
        )

    async def list_objects(request: web.Request) -> web.Response:
        assert "b3" in request.headers
        assert request.match_info["bucket"] == "foo"

        res: Dict[str, Any]
        prefix = request.query.get("prefix", "")
        contents = [
            with_keys(item, LIST_KEYS)
            for item in CONTENTS.values()
            if item["key"].startswith(prefix)
        ]
        common_prefixes: Set[str] = set()
        if request.query["recursive"] == "false":
            new_contents = []
            for item in contents:
                pos = item["key"].find("/", len(prefix))
                if pos != -1:
                    common_prefixes.add(item["key"][: pos + 1])
                else:
                    new_contents.append(item)
            contents = new_contents

        return web.json_response(
            {
                "contents": sorted(contents, key=lambda x: x["key"]),
                "common_prefixes": [{"prefix": p} for p in common_prefixes],
                "is_truncated": False,
            }
        )

    async def get_object(request: web.Request) -> web.StreamResponse:
        assert "b3" in request.headers
        assert request.match_info["bucket"] == "foo"

        key = request.match_info["path"]
        if key not in CONTENTS:
            raise web.HTTPNotFound()
        obj = CONTENTS[key]

        resp = web.StreamResponse(status=200)
        etag = hashlib.md5(obj["body"]).hexdigest()
        resp.headers.update({"ETag": repr(etag)})
        resp.last_modified = obj["last_modified"]
        resp.content_length = len(obj["body"])
        resp.content_type = "plain/text"
        await resp.prepare(request)
        await resp.write(obj["body"])
        return resp

    async def put_object(request: web.Request) -> web.Response:
        assert "b3" in request.headers
        assert request.match_info["bucket"] == "foo"

        key = request.match_info["path"]
        body = await request.content.read()
        obj = {
            "key": key,
            "size": len(body),
            "last_modified": datetime.now().timestamp(),
            "body": body,
        }
        CONTENTS[key] = obj
        etag = hashlib.md5(obj["body"]).hexdigest()

        return web.Response(headers={"ETag": repr(etag)})

    app = web.Application()
    app.router.add_get(OBSUrlRotes.LIST_BUCKETS, list_buckets)
    app.router.add_get(OBSUrlRotes.LIST_OBJECTS, list_objects)
    # HEAD will also use this
    app.router.add_get(OBSUrlRotes.GET_OBJECT, get_object)
    app.router.add_put(OBSUrlRotes.PUT_OBJECT, put_object)

    return await aiohttp_server(app)


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
            name="foo", creation_time=int(mtime1.timestamp()), permission=Action.READ,
        ),
        BucketListing(
            name="bar", creation_time=int(mtime2.timestamp()), permission=Action.READ,
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
            body=async_iter(),
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
    assert (await calc_md5(txt_file))[0] == body_md5


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
    assert (await calc_md5(txt_file))[0] == body_md5


# high level API


async def test_object_storage_upload_file_does_not_exists(
    make_client: _MakeClient,
) -> None:
    async with make_client("https://example.com") as client:
        with pytest.raises(FileNotFoundError):
            await client.object_storage.upload_file(
                URL("file:///not-exists-file"), URL("object://host/path/to/file.txt")
            )


async def test_object_storage_upload_dir_doesnt_exist(make_client: _MakeClient) -> None:
    async with make_client("https://example.com") as client:
        with pytest.raises(IsADirectoryError):
            await client.object_storage.upload_file(
                URL(FOLDER.as_uri()), URL("object://host/path/to")
            )


async def test_object_storage_upload_not_a_file(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
) -> None:

    file_path = Path(os.devnull).absolute()
    progress = mock.Mock()

    async with make_client(object_storage_server.make_url("/")) as client:
        await client.object_storage.upload_file(
            URL(file_path.as_uri()), URL("object:foo/file.txt"), progress=progress
        )

    uploaded = object_storage_contents["file.txt"]
    assert uploaded["body"] == b""

    src = URL(file_path.as_uri())
    dst = URL("object://foo/file.txt")
    progress.start.assert_called_with(StorageProgressStart(src, dst, 0))
    progress.step.assert_not_called()
    progress.complete.assert_called_with(StorageProgressComplete(src, dst, 0))


async def test_object_storage_upload_regular_file_new_file(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
) -> None:
    file_path = DATA_FOLDER / "file.txt"
    file_size = file_path.stat().st_size
    progress = mock.Mock()

    async with make_client(object_storage_server.make_url("/")) as client:
        await client.object_storage.upload_file(
            URL(file_path.as_uri()), URL("object:foo/file.txt"), progress=progress
        )

    expected = file_path.read_bytes()
    uploaded = object_storage_contents["file.txt"]
    assert uploaded["body"] == expected

    src = URL(file_path.as_uri())
    dst = URL("object://foo/file.txt")
    progress.start.assert_called_with(StorageProgressStart(src, dst, file_size))
    progress.step.assert_called_with(
        StorageProgressStep(src, dst, file_size, file_size)
    )
    progress.complete.assert_called_with(StorageProgressComplete(src, dst, file_size))


async def test_object_storage_upload_large_file(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
    tmp_path: Path,
) -> None:
    local_dir = tmp_path / "local"
    local_dir.mkdir(exist_ok=True)
    local_file = local_dir / "file.txt"

    with local_file.open("wb") as f:
        for i in range(1024):
            f.write(b"yncuNRzU0xhKSqIh" * (4 * 1024))

    progress = mock.Mock()

    async with make_client(object_storage_server.make_url("/")) as client:
        await client.object_storage.upload_file(
            URL(local_file.as_uri()),
            URL("object:foo/folder2/big_file"),
            progress=progress,
        )

    expected = local_file.read_bytes()
    uploaded = object_storage_contents["folder2/big_file"]
    assert uploaded["body"] == expected

    src = URL(local_file.as_uri())
    dst = URL("object://foo/folder2/big_file")
    file_size = len(expected)
    progress.start.assert_called_with(StorageProgressStart(src, dst, file_size))
    progress.step.assert_called_with(
        StorageProgressStep(src, dst, file_size, file_size)
    )
    progress.complete.assert_called_with(StorageProgressComplete(src, dst, file_size))


async def test_object_storage_upload_regular_file_to_existing_file(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
) -> None:
    file_path = DATA_FOLDER / "file.txt"

    async with make_client(object_storage_server.make_url("/")) as client:
        await client.object_storage.upload_file(
            URL(file_path.as_uri()), URL("object:foo/test1.txt")
        )

    expected = file_path.read_bytes()
    uploaded = object_storage_contents["test1.txt"]
    assert uploaded["body"] == expected


async def test_object_storage_upload_regular_file_to_existing_dir_with_slash(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
) -> None:
    file_path = DATA_FOLDER / "file.txt"

    async with make_client(object_storage_server.make_url("/")) as client:
        with pytest.raises(IsADirectoryError):
            await client.object_storage.upload_file(
                URL(file_path.as_uri()), URL("object:foo/empty/")
            )


async def test_object_storage_upload_regular_file_to_existing_dir_without_slash(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
) -> None:
    file_path = DATA_FOLDER / "file.txt"

    async with make_client(object_storage_server.make_url("/")) as client:
        with pytest.raises(IsADirectoryError):
            await client.object_storage.upload_file(
                URL(file_path.as_uri()), URL("object:foo/empty")
            )


async def test_object_storage_upload_regular_file_to_existing_non_dir(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
) -> None:
    file_path = DATA_FOLDER / "file.txt"

    async with make_client(object_storage_server.make_url("/")) as client:
        with pytest.raises(NotADirectoryError):
            await client.object_storage.upload_file(
                URL(file_path.as_uri()), URL("object:foo/test1.txt/subfile.txt")
            )


async def test_object_storage_upload_regular_file_to_not_existing(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
) -> None:
    # In object storage it's perfectly fine to upload on non-exising path
    file_path = DATA_FOLDER / "file.txt"

    async with make_client(object_storage_server.make_url("/")) as client:
        await client.object_storage.upload_file(
            URL(file_path.as_uri()), URL("object:foo/absent-dir/absent-file.txt")
        )

    expected = file_path.read_bytes()
    uploaded = object_storage_contents["absent-dir/absent-file.txt"]
    assert uploaded["body"] == expected


async def test_object_storage_upload_recursive_src_doesnt_exist(
    make_client: _MakeClient,
) -> None:
    async with make_client("https://example.com") as client:
        with pytest.raises(FileNotFoundError):
            await client.object_storage.upload_dir(
                URL("file:does_not_exist"), URL("object://host/path/to")
            )


async def test_object_storage_upload_recursive_src_is_a_file(
    make_client: _MakeClient,
) -> None:
    file_path = DATA_FOLDER / "file.txt"

    async with make_client("https://example.com") as client:
        with pytest.raises(NotADirectoryError):
            await client.object_storage.upload_dir(
                URL(file_path.as_uri()), URL("object://host/path/to")
            )


async def test_object_storage_upload_recursive_target_is_a_file(
    object_storage_server: Any, make_client: _MakeClient,
) -> None:

    async with make_client(object_storage_server.make_url("/")) as client:
        with pytest.raises(NotADirectoryError):
            await client.object_storage.upload_dir(
                URL(DATA_FOLDER.as_uri()), URL("object:foo/test1.txt")
            )


async def test_object_storage_upload_empty_dir(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "empty"
    src_dir.mkdir()
    assert list(src_dir.iterdir()) == []

    async with make_client(object_storage_server.make_url("/")) as client:
        await client.object_storage.upload_dir(
            URL(src_dir.as_uri()), URL("object:foo/folder")
        )

    assert "folder" not in object_storage_contents
    uploaded = object_storage_contents["folder/"]
    assert uploaded == {
        "key": "folder/",
        "size": 0,
        "last_modified": mock.ANY,
        "body": b"",
    }


async def test_object_storage_upload_recursive_ok(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
) -> None:

    async with make_client(object_storage_server.make_url("/")) as client:
        await client.object_storage.upload_dir(
            URL(DATA_FOLDER.as_uri()) / "nested", URL("object:foo/folder")
        )

    keys = [v for k, v in object_storage_contents.items() if k.startswith("folder/")]
    assert keys == [
        {"key": "folder/", "size": 0, "last_modified": mock.ANY, "body": b""},
        {"key": "folder/folder/", "size": 0, "last_modified": mock.ANY, "body": b""},
        {
            "key": "folder/folder/file.txt",
            "size": 20,
            "last_modified": mock.ANY,
            "body": b"Nested file content\n",
        },
    ]


async def test_object_storage_upload_recursive_slash_ending(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
) -> None:

    async with make_client(object_storage_server.make_url("/")) as client:
        await client.object_storage.upload_dir(
            URL(DATA_FOLDER.as_uri()) / "nested", URL("object:foo/folder/")
        )

    keys = [v for k, v in object_storage_contents.items() if k.startswith("folder/")]
    assert keys == [
        {"key": "folder/", "size": 0, "last_modified": mock.ANY, "body": b""},
        {"key": "folder/folder/", "size": 0, "last_modified": mock.ANY, "body": b""},
        {
            "key": "folder/folder/file.txt",
            "size": 20,
            "last_modified": mock.ANY,
            "body": b"Nested file content\n",
        },
    ]


async def test_object_storage_download_regular_file_to_absent_file(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
    tmp_path: Path,
) -> None:
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    local_file = local_dir / "file.txt"
    progress = mock.Mock()

    async with make_client(object_storage_server.make_url("/")) as client:
        await client.object_storage.download_file(
            URL("object:foo/test1.txt"), URL(local_file.as_uri()), progress=progress
        )

    expected = object_storage_contents["test1.txt"]["body"]
    downloaded = local_file.read_bytes()
    assert downloaded == expected

    src = URL("object://foo/test1.txt")
    dst = URL(local_file.as_uri())
    file_size = len(expected)
    progress.start.assert_called_with(StorageProgressStart(src, dst, file_size))
    progress.step.assert_called_with(
        StorageProgressStep(src, dst, file_size, file_size)
    )
    progress.complete.assert_called_with(StorageProgressComplete(src, dst, file_size))


async def test_object_storage_download_large_file(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
    tmp_path: Path,
) -> None:
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    local_file = local_dir / "file.txt"
    progress = mock.Mock()

    # 16 * 4 = 64 MB of data
    large_payload = b"yncuNRzU0xhKSqIh" * (4 * 1024 * 1024)
    object_storage_contents["folder2/big_file"] = {
        "key": "folder2/big_file",
        "size": len(large_payload),
        "last_modified": datetime(2019, 1, 3).timestamp(),
        "body": large_payload,
    }

    async with make_client(object_storage_server.make_url("/")) as client:
        await client.object_storage.download_file(
            URL("object:foo/folder2/big_file"),
            URL(local_file.as_uri()),
            progress=progress,
        )

    downloaded = local_file.read_bytes()
    assert downloaded == large_payload

    src = URL("object://foo/folder2/big_file")
    dst = URL(local_file.as_uri())
    file_size = len(large_payload)
    progress.start.assert_called_with(StorageProgressStart(src, dst, file_size))
    progress.step.assert_called_with(
        StorageProgressStep(src, dst, file_size, file_size)
    )
    progress.complete.assert_called_with(StorageProgressComplete(src, dst, file_size))


async def test_object_storage_download_regular_file_to_existing_file(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
    tmp_path: Path,
) -> None:
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    local_file = local_dir / "file.txt"
    local_file.write_bytes(b"Previous data")

    async with make_client(object_storage_server.make_url("/")) as client:
        await client.object_storage.download_file(
            URL("object:foo/test1.txt"), URL(local_file.as_uri())
        )

    expected = object_storage_contents["test1.txt"]["body"]
    downloaded = local_file.read_bytes()
    assert downloaded == expected


async def test_object_storage_download_regular_file_to_dir(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
    tmp_path: Path,
) -> None:
    local_dir = tmp_path / "local"
    local_dir.mkdir()

    async with make_client(object_storage_server.make_url("/")) as client:
        with pytest.raises(IsADirectoryError):
            await client.object_storage.download_file(
                URL("object:foo/test1.txt"), URL(local_dir.as_uri())
            )


async def test_object_storage_download_regular_file_to_dir_slash_ended(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
    tmp_path: Path,
) -> None:
    local_dir = tmp_path / "local"
    local_dir.mkdir()

    async with make_client(object_storage_server.make_url("/")) as client:
        with pytest.raises(IsADirectoryError):
            await client.object_storage.download_file(
                URL("object:foo/test1.txt"), URL(local_dir.as_uri() + "/")
            )


async def test_object_storage_download_regular_file_to_non_file(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
    tmp_path: Path,
) -> None:

    async with make_client(object_storage_server.make_url("/")) as client:
        await client.object_storage.download_file(
            URL("object:foo/test1.txt"), URL(Path(os.devnull).absolute().as_uri())
        )


async def test_object_storage_download_empty_dir(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "empty"
    assert not target_dir.exists()

    async with make_client(object_storage_server.make_url("/")) as client:
        await client.object_storage.download_dir(
            URL("object:foo/empty"), URL(target_dir.as_uri())
        )

    assert list(target_dir.iterdir()) == []


async def test_object_storage_download_dir(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
    tmp_path: Path,
) -> None:
    local_dir = tmp_path / "local"
    local_dir.mkdir()

    async with make_client(object_storage_server.make_url("/")) as client:
        await client.object_storage.download_dir(
            URL("object:foo"), URL(local_dir.as_uri())
        )

    files = sorted(dir_list(local_dir), key=lambda x: x["path"])
    assert files == [
        {"dir": True, "path": "empty"},
        {"dir": True, "path": "folder1"},
        {"body": b"w", "dir": False, "path": "folder1/xxx.txt", "size": 1},
        {"body": b"bb", "dir": False, "path": "folder1/yyy.json", "size": 2},
        {"body": b"w" * 213, "dir": False, "path": "test.json", "size": 213},
        {"body": b"w" * 111, "dir": False, "path": "test1.txt", "size": 111},
        {"body": b"w" * 222, "dir": False, "path": "test2.txt", "size": 222},
    ]


async def test_object_storage_download_dir_with_slash(
    object_storage_server: Any,
    make_client: _MakeClient,
    object_storage_contents: _ContentsObj,
    tmp_path: Path,
) -> None:
    local_dir = tmp_path / "local"
    local_dir.mkdir()

    async with make_client(object_storage_server.make_url("/")) as client:
        await client.object_storage.download_dir(
            URL("object:foo"), URL(local_dir.as_uri() + "/")
        )

    files = sorted(dir_list(local_dir), key=lambda x: x["path"])
    assert files == [
        {"dir": True, "path": "empty"},
        {"dir": True, "path": "folder1"},
        {"body": b"w", "dir": False, "path": "folder1/xxx.txt", "size": 1},
        {"body": b"bb", "dir": False, "path": "folder1/yyy.json", "size": 2},
        {"body": b"w" * 213, "dir": False, "path": "test.json", "size": 213},
        {"body": b"w" * 111, "dir": False, "path": "test1.txt", "size": 111},
        {"body": b"w" * 222, "dir": False, "path": "test2.txt", "size": 222},
    ]
