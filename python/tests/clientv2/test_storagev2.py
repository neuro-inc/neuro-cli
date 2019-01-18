from pathlib import Path

import pytest
from aiohttp import web
from yarl import URL

from neuromation.clientv2 import AbstractProgress, ClientV2, FileStatus, FileStatusType


FOLDER = Path(__file__).parent
DATA_FOLDER = FOLDER / "data"


class DummyProgress(AbstractProgress):
    def start(self, file: str, size: int) -> None:
        pass

    def complete(self, file: str) -> None:
        pass

    def progress(self, file: str, current: int) -> None:
        pass


@pytest.fixture
async def storage_server(aiohttp_raw_server, tmp_path):
    PREFIX = "/storage/user"
    PREFIX_LEN = len(PREFIX)

    async def handler(request):
        op = request.query["op"]
        path = request.path
        assert path.startswith(PREFIX)
        path = path[PREFIX_LEN:]
        if path.startswith("/"):
            path = path[1:]
        local_path = tmp_path / path
        if op == "CREATE":
            content = await request.read()
            local_path.write_bytes(content)
            return web.Response(status=201)
        elif op == "OPEN":
            return web.Response(body=local_path.read_bytes())
        elif op == "GETFILESTATUS":
            if not local_path.exists():
                raise web.HTTPNotFound()
            stat = local_path.stat()
            return web.json_response(
                {
                    "FileStatus": {
                        "path": local_path.name,
                        "type": "FILE" if local_path.is_file() else "DIRECTORY",
                        "length": stat.st_size,
                        "modificationTime": stat.st_mtime,
                        "permission": "write",
                    }
                }
            )
        else:
            raise web.HTTPInternalServerError(text=f"Unsupported operation {op}")

    return await aiohttp_raw_server(handler)


async def test_uri_to_path_non_storage(token):
    async with ClientV2(URL("https://example.com"), token) as client:
        with pytest.raises(ValueError):
            client.storage._uri_to_path(URL("bad-schema://something"))


async def test_uri_to_path_home(token):
    async with ClientV2(URL("https://example.com"), token) as client:
        assert client.storage._uri_to_path(URL("storage://~/path")) == "user/path"


async def test_uri_to_path_no_user(token):
    async with ClientV2(URL("https://example.com"), token) as client:
        assert client.storage._uri_to_path(URL("storage:/data")) == "user/data"


async def test_uri_to_path_explicit_user(token):
    async with ClientV2(URL("https://example.com"), token) as client:
        assert client.storage._uri_to_path(URL("storage://alice/data")) == "alice/data"


async def test_uri_to_path_to_file(token):
    async with ClientV2(URL("https://example.com"), token) as client:
        assert (
            client.storage._uri_to_path(URL("storage://alice/data/foo.txt"))
            == "alice/data/foo.txt"
        )


async def test_uri_to_path_strip_slash(token):
    async with ClientV2(URL("https://example.com"), token) as client:
        assert (
            client.storage._uri_to_path(URL("storage://alice/data/foo.txt/"))
            == "alice/data/foo.txt"
        )


async def test_uri_to_path_root(token):
    async with ClientV2(URL("https://example.com"), token) as client:
        assert client.storage._uri_to_path(URL("storage:")) == "user"


async def test_uri_to_path_root2(token):
    async with ClientV2(URL("https://example.com"), token) as client:
        assert client.storage._uri_to_path(URL("storage:/")) == "user"


async def test_uri_to_path_root3(token):
    async with ClientV2(URL("https://example.com"), token) as client:
        assert client.storage._uri_to_path(URL("storage://")) == "user"


@pytest.mark.xfail
async def test_uri_to_path_root4(token):
    async with ClientV2(URL("https://example.com"), token) as client:
        assert client.storage._uri_to_path(URL("storage:///")) == "/"


async def test_uri_to_path_relative(token):
    async with ClientV2(URL("https://example.com"), token) as client:
        assert client.storage._uri_to_path(URL("storage:path")) == "user/path"


async def test_storage_ls(aiohttp_server, token):
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

    async with ClientV2(srv.make_url("/"), token) as client:
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


async def test_storage_rm(aiohttp_server, token):
    async def handler(request):
        assert request.path == "/storage/user/folder"
        assert request.query == {"op": "DELETE"}
        return web.Response(status=204)

    app = web.Application()
    app.router.add_delete("/storage/user/folder", handler)

    srv = await aiohttp_server(app)

    async with ClientV2(srv.make_url("/"), token) as client:
        await client.storage.rm(URL("storage://~/folder"))


async def test_storage_mv(aiohttp_server, token):
    async def handler(request):
        assert request.path == "/storage/user/folder"
        assert request.query == {"op": "RENAME", "destination": "/user/other"}
        return web.Response(status=204)

    app = web.Application()
    app.router.add_post("/storage/user/folder", handler)

    srv = await aiohttp_server(app)

    async with ClientV2(srv.make_url("/"), token) as client:
        await client.storage.mv(URL("storage://~/folder"), URL("storage://~/other"))


async def test_storage_mkdir(aiohttp_server, token):
    async def handler(request):
        assert request.path == "/storage/user/folder"
        assert request.query == {"op": "MKDIRS"}
        return web.Response(status=204)

    app = web.Application()
    app.router.add_put("/storage/user/folder", handler)

    srv = await aiohttp_server(app)

    async with ClientV2(srv.make_url("/"), token) as client:
        await client.storage.mkdirs(URL("storage://~/folder"))


async def test_storage_create(aiohttp_server, token):
    async def handler(request):
        assert request.path == "/storage/user/file"
        assert request.query == {"op": "CREATE"}
        content = await request.read()
        assert content == b"01234"
        return web.Response(status=201)

    app = web.Application()
    app.router.add_put("/storage/user/file", handler)

    srv = await aiohttp_server(app)

    async def gen():
        for i in range(5):
            yield str(i).encode("ascii")

    async with ClientV2(srv.make_url("/"), token) as client:
        await client.storage.create(URL("storage://~/file"), gen())


async def test_storage_stats(aiohttp_server, token):
    async def handler(request):
        assert request.path == "/storage/user/folder"
        assert request.query == {"op": "GETFILESTATUS"}
        return web.json_response(
            {
                "FileStatus": {
                    "path": "/user/folder",
                    "type": "DIRECTORY",
                    "length": 1234,
                    "modificationTime": 3456,
                    "permission": "read",
                }
            }
        )

    app = web.Application()
    app.router.add_get("/storage/user/folder", handler)

    srv = await aiohttp_server(app)

    async with ClientV2(srv.make_url("/"), token) as client:
        stats = await client.storage.stats(URL("storage://~/folder"))
        assert stats == FileStatus(
            path="/user/folder",
            type=FileStatusType.DIRECTORY,
            size=1234,
            modification_time=3456,
            permission="read",
        )


async def test_storage_open(aiohttp_server, token):
    async def handler(request):
        assert request.path == "/storage/user/file"
        if request.query["op"] == "OPEN":
            resp = web.StreamResponse()
            await resp.prepare(request)
            for i in range(5):
                await resp.write(str(i).encode("ascii"))
            return resp
        elif request.query["op"] == "GETFILESTATUS":
            return web.json_response(
                {
                    "FileStatus": {
                        "path": "/user/file",
                        "type": "FILE",
                        "length": 5,
                        "modificationTime": 3456,
                        "permission": "read",
                    }
                }
            )
        else:
            raise AssertionError(f"Unknown operation {request.query['op']}")

    app = web.Application()
    app.router.add_get("/storage/user/file", handler)

    srv = await aiohttp_server(app)

    async with ClientV2(srv.make_url("/"), token) as client:
        buf = bytearray()
        async for chunk in client.storage.open(URL("storage://~/file")):
            buf.extend(chunk)
        assert buf == b"01234"


async def test_storage_open_directory(aiohttp_server, token):
    async def handler(request):
        assert request.path == "/storage/user/folder"
        assert request.query == {"op": "GETFILESTATUS"}
        return web.json_response(
            {
                "FileStatus": {
                    "path": "/user/folder",
                    "type": "DIRECTORY",
                    "length": 5,
                    "modificationTime": 3456,
                    "permission": "read",
                }
            }
        )

    app = web.Application()
    app.router.add_get("/storage/user/folder", handler)

    srv = await aiohttp_server(app)

    async with ClientV2(srv.make_url("/"), token) as client:
        buf = bytearray()
        with pytest.raises(IsADirectoryError):
            async for chunk in client.storage.open(URL("storage://~/folder")):
                buf.extend(chunk)
        assert not buf


# test normalizers


async def test_storage_normalize(token):
    async with ClientV2("https://example.com", token) as client:
        url = client.storage.normalize(URL("storage:path/to/file.txt"))
        assert url.scheme == "storage"
        assert url.host is None
        assert url.path == "path/to/file.txt"


async def test_storage_normalize_home_dir(token):
    async with ClientV2("https://example.com", token) as client:
        url = client.storage.normalize(URL("storage://~/file.txt"))
        assert url.scheme == "storage"
        assert url.host == "user"
        assert url.path == "/file.txt"


async def test_storage_normalize_bad_scheme(token):
    async with ClientV2("https://example.com", token) as client:
        with pytest.raises(
            ValueError, match="Path should be targeting platform storage."
        ):
            client.storage.normalize(URL("other:path/to/file.txt"))


@pytest.mark.xfail
async def test_storage_normalize_local(token):
    async with ClientV2("https://example.com", token) as client:
        url = client.storage.normalize_local(URL("file:///path/to/file.txt"))
        assert url.scheme == "file"
        assert url.host is None
        # fails on CI only :(
        assert url.path == "/path/to/file.txt"


async def test_storage_normalize_local_bad_scheme(token):
    async with ClientV2("https://example.com", token) as client:
        with pytest.raises(
            ValueError, match="Path should be targeting local file system."
        ):
            client.storage.normalize_local(URL("other:path/to/file.txt"))


@pytest.mark.xfail
async def test_storage_normalize_local_expand_user(token, monkeypatch):
    monkeypatch.setenv("HOME", "/home/user")
    async with ClientV2("https://example.com", token) as client:
        url = client.storage.normalize_local(URL("file:~/path/to/file.txt"))
        assert url.scheme == "file"
        assert url.host is None
        # fails on CI only :(
        assert url.path == "/home/user/path/to/file.txt"


async def test_storage_normalize_local_with_host(token):
    async with ClientV2("https://example.com", token) as client:
        with pytest.raises(ValueError, match="Host part is not allowed"):
            client.storage.normalize_local(URL("file://host/path/to/file.txt"))


# high level API


async def test_storage_upload_file_does_not_exists(token):
    async with ClientV2("https://example.com", token) as client:
        with pytest.raises(FileNotFoundError):
            await client.storage.upload_file(
                DummyProgress(),
                URL("file:///not-exists-file"),
                URL("storage://host/path/to/file.txt"),
            )


async def test_storage_upload_dir_doesnt_exist(token):
    async with ClientV2("https://example.com", token) as client:
        with pytest.raises(IsADirectoryError):
            await client.storage.upload_file(
                DummyProgress(), URL(FOLDER.as_uri()), URL("storage://host/path/to")
            )


async def test_storage_upload_not_a_file(token):
    async with ClientV2("https://example.com", token) as client:
        with pytest.raises(OSError):
            await client.storage.upload_file(
                DummyProgress(),
                URL("file:///dev/random"),
                URL("storage://host/path/to"),
            )


async def test_storage_upload_regular_file_to_existing_file_target(
    storage_server, token, tmp_path
):
    FILE_PATH = DATA_FOLDER / "file.txt"
    TARGET_PATH = tmp_path / "file.txt"

    async with ClientV2(storage_server.make_url("/"), token) as client:
        await client.storage.upload_file(
            DummyProgress(), URL(FILE_PATH.as_uri()), URL("storage:file.txt")
        )

    expected = FILE_PATH.read_bytes()
    uploaded = TARGET_PATH.read_bytes()
    assert uploaded == expected


async def test_storage_upload_regular_file_to_existing_dir(
    storage_server, token, tmp_path
):
    FILE_PATH = DATA_FOLDER / "file.txt"
    DIR = tmp_path / "folder"
    DIR.mkdir()
    TARGET_PATH = DIR / "file.txt"

    async with ClientV2(storage_server.make_url("/"), token) as client:
        await client.storage.upload_file(
            DummyProgress(), URL(FILE_PATH.as_uri()), URL("storage:folder")
        )

    expected = FILE_PATH.read_bytes()
    uploaded = TARGET_PATH.read_bytes()
    assert uploaded == expected


async def test_storage_upload_regular_file_to_existing_file(
    storage_server, token, tmp_path
):
    FILE_PATH = DATA_FOLDER / "file.txt"
    DIR = tmp_path / "folder"
    DIR.mkdir()
    TARGET_PATH = DIR / "file.txt"
    TARGET_PATH.write_bytes(b"existing file")

    async with ClientV2(storage_server.make_url("/"), token) as client:
        await client.storage.upload_file(
            DummyProgress(), URL(FILE_PATH.as_uri()), URL("storage:folder/file.txt")
        )

    expected = FILE_PATH.read_bytes()
    uploaded = TARGET_PATH.read_bytes()
    assert uploaded == expected


async def test_storage_upload_regular_file_to_existing_dir_with_trailing_slash(
    storage_server, token, tmp_path
):
    FILE_PATH = DATA_FOLDER / "file.txt"
    DIR = tmp_path / "folder"
    DIR.mkdir()
    TARGET_PATH = DIR / "file.txt"

    async with ClientV2(storage_server.make_url("/"), token) as client:
        await client.storage.upload_file(
            DummyProgress(), URL(FILE_PATH.as_uri()), URL("storage:folder/")
        )

    expected = FILE_PATH.read_bytes()
    uploaded = TARGET_PATH.read_bytes()
    assert uploaded == expected


async def test_storage_upload_regular_file_to_existing_non_dir(
    storage_server, token, tmp_path
):
    FILE_PATH = DATA_FOLDER / "file.txt"
    path = tmp_path / "file"
    path.write_bytes(b"dummy")

    async with ClientV2(storage_server.make_url("/"), token) as client:
        with pytest.raises(NotADirectoryError):
            await client.storage.upload_file(
                DummyProgress(),
                URL(FILE_PATH.as_uri()),
                URL("storage:file/subfile.txt"),
            )


async def test_storage_upload_regular_file_to_not_existing(
    storage_server, token, tmp_path
):
    FILE_PATH = DATA_FOLDER / "file.txt"

    async with ClientV2(storage_server.make_url("/"), token) as client:
        with pytest.raises(NotADirectoryError):
            await client.storage.upload_file(
                DummyProgress(),
                URL(FILE_PATH.as_uri()),
                URL("storage:absent-dir/absent-file.txt"),
            )


async def test_storage_upload_recursive_src_doesnt_exist(token):
    async with ClientV2("https://example.com", token) as client:
        with pytest.raises(FileNotFoundError):
            await client.storage.upload_dir(
                DummyProgress(),
                URL("file:does_not_exist"),
                URL("storage://host/path/to"),
            )
