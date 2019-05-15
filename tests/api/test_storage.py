from filecmp import dircmp
from pathlib import Path
from shutil import copytree
from typing import Any, AsyncIterator, Callable, List, Tuple
from unittest import mock

import pytest
from aiohttp import web
from yarl import URL

from neuromation.api import Client, FileStatus, FileStatusType
from tests import _RawTestServerFactory, _TestServerFactory


_MakeClient = Callable[..., Client]


FOLDER = Path(__file__).parent
DATA_FOLDER = FOLDER / "data"


def calc_diff(dcmp: "dircmp[str]", *, pre: str = "") -> List[Tuple[str, str]]:
    ret = []
    for name in dcmp.diff_files:
        ret.append((pre + name, pre + name))
    for name in dcmp.left_only:
        ret.append((pre + name, ""))
    for name in dcmp.right_only:
        ret.append(("", pre + name))
    for name, sub_dcmp in dcmp.subdirs.items():
        ret.extend(calc_diff(sub_dcmp, pre=name + "/"))
    return ret


@pytest.fixture
def storage_path(tmp_path: Path) -> Path:
    ret = tmp_path / "storage"
    ret.mkdir()
    return ret


@pytest.fixture
async def storage_server(
    aiohttp_raw_server: _RawTestServerFactory, storage_path: Path
) -> Any:
    PREFIX = "/storage/user"
    PREFIX_LEN = len(PREFIX)

    async def handler(request: web.Request) -> web.Response:
        op = request.query["op"]
        path = request.path
        assert path.startswith(PREFIX)
        path = path[PREFIX_LEN:]
        if path.startswith("/"):
            path = path[1:]
        local_path = storage_path / path
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
        elif op == "MKDIRS":
            local_path.mkdir(parents=True, exist_ok=True)
            return web.Response(status=201)
        elif op == "LISTSTATUS":
            ret = []
            for child in local_path.iterdir():
                stat = child.stat()
                ret.append(
                    {
                        "path": child.name,
                        "type": "FILE" if child.is_file() else "DIRECTORY",
                        "length": stat.st_size,
                        "modificationTime": stat.st_mtime,
                        "permission": "write",
                    }
                )
            return web.json_response({"FileStatuses": {"FileStatus": ret}})
        else:
            raise web.HTTPInternalServerError(text=f"Unsupported operation {op}")

    return await aiohttp_raw_server(handler)


async def test_storage_ls(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
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
                    "type": "DIRECTORY",
                    "modificationTime": 0,
                    "permission": "read",
                },
            ]
        }
    }

    async def handler(request: web.Request) -> web.Response:
        assert request.path == "/storage/user/folder"
        assert request.query == {"op": "LISTSTATUS"}
        return web.json_response(JSON)

    app = web.Application()
    app.router.add_get("/storage/user/folder", handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        ret = await client.storage.ls(URL("storage://~/folder"))

    assert ret == [
        FileStatus(
            path="foo",
            size=1024,
            type=FileStatusType.FILE,
            modification_time=0,
            permission="read",
        ),
        FileStatus(
            path="bar",
            size=4 * 1024,
            type=FileStatusType.DIRECTORY,
            modification_time=0,
            permission="read",
        ),
    ]


async def test_storage_rm(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handler(request: web.Request) -> web.Response:
        assert request.path == "/storage/user/folder"
        assert request.query == {"op": "DELETE"}
        return web.Response(status=204)

    app = web.Application()
    app.router.add_delete("/storage/user/folder", handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        await client.storage.rm(URL("storage://~/folder"))


async def test_storage_mv(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handler(request: web.Request) -> web.Response:
        assert request.path == "/storage/user/folder"
        assert request.query == {"op": "RENAME", "destination": "/user/other"}
        return web.Response(status=204)

    app = web.Application()
    app.router.add_post("/storage/user/folder", handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        await client.storage.mv(URL("storage://~/folder"), URL("storage://~/other"))


async def test_storage_mkdir_parents_exist_ok(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handler(request: web.Request) -> web.Response:
        assert request.path == "/storage/user/folder/sub"
        assert request.query == {"op": "MKDIRS"}
        return web.Response(status=204)

    app = web.Application()
    app.router.add_put("/storage/user/folder/sub", handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        await client.storage.mkdirs(
            URL("storage://~/folder/sub"), parents=True, exist_ok=True
        )


async def test_storage_mkdir_parents(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def get_handler(request: web.Request) -> web.Response:
        assert request.path == "/storage/user/folder/sub"
        assert request.query == {"op": "GETFILESTATUS"}
        return web.Response(status=404)

    async def put_handler(request: web.Request) -> web.Response:
        assert request.path == "/storage/user/folder/sub"
        assert request.query == {"op": "MKDIRS"}
        return web.Response(status=204)

    app = web.Application()
    app.router.add_get("/storage/user/folder/sub", get_handler)
    app.router.add_put("/storage/user/folder/sub", put_handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        await client.storage.mkdirs(URL("storage://~/folder/sub"), parents=True)


async def test_storage_mkdir_exist_ok(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def get_handler(request: web.Request) -> web.Response:
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

    async def put_handler(request: web.Request) -> web.Response:
        assert request.path == "/storage/user/folder/sub"
        assert request.query == {"op": "MKDIRS"}
        return web.Response(status=204)

    app = web.Application()
    app.router.add_get("/storage/user/folder", get_handler)
    app.router.add_put("/storage/user/folder/sub", put_handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        await client.storage.mkdirs(URL("storage://~/folder/sub"), exist_ok=True)


async def test_storage_mkdir(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def get_handler(request: web.Request) -> web.Response:
        assert request.path == "/storage/user/folder/sub"
        assert request.query == {"op": "GETFILESTATUS"}
        return web.Response(status=404)

    async def parent_get_handler(request: web.Request) -> web.Response:
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

    async def put_handler(request: web.Request) -> web.Response:
        assert request.path == "/storage/user/folder/sub"
        assert request.query == {"op": "MKDIRS"}
        return web.Response(status=204)

    app = web.Application()
    app.router.add_get("/storage/user/folder/sub", get_handler)
    app.router.add_get("/storage/user/folder", parent_get_handler)
    app.router.add_put("/storage/user/folder/sub", put_handler)

    srv = await aiohttp_server(app)

    async with make_client(srv.make_url("/")) as client:
        await client.storage.mkdirs(URL("storage://~/folder/sub"))


async def test_storage_create(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handler(request: web.Request) -> web.Response:
        assert request.path == "/storage/user/file"
        assert request.query == {"op": "CREATE"}
        content = await request.read()
        assert content == b"01234"
        return web.Response(status=201)

    app = web.Application()
    app.router.add_put("/storage/user/file", handler)

    srv = await aiohttp_server(app)

    async def gen() -> AsyncIterator[bytes]:
        for i in range(5):
            yield str(i).encode("ascii")

    async with make_client(srv.make_url("/")) as client:
        await client.storage.create(URL("storage://~/file"), gen())


async def test_storage_stats(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handler(request: web.Request) -> web.Response:
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

    async with make_client(srv.make_url("/")) as client:
        stats = await client.storage.stats(URL("storage://~/folder"))
        assert stats == FileStatus(
            path="/user/folder",
            type=FileStatusType.DIRECTORY,
            size=1234,
            modification_time=3456,
            permission="read",
        )


async def test_storage_open(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handler(request: web.Request) -> web.StreamResponse:
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

    async with make_client(srv.make_url("/")) as client:
        buf = bytearray()
        async for chunk in client.storage.open(URL("storage://~/file")):
            buf.extend(chunk)
        assert buf == b"01234"


async def test_storage_open_directory(
    aiohttp_server: _TestServerFactory, make_client: _MakeClient
) -> None:
    async def handler(request: web.Request) -> web.Response:
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

    async with make_client(srv.make_url("/")) as client:
        buf = bytearray()
        with pytest.raises(IsADirectoryError):
            async for chunk in client.storage.open(URL("storage://~/folder")):
                buf.extend(chunk)
        assert not buf


# test normalizers


# high level API


async def test_storage_upload_file_does_not_exists(make_client: _MakeClient) -> None:
    async with make_client("https://example.com") as client:
        with pytest.raises(FileNotFoundError):
            await client.storage.upload_file(
                URL("file:///not-exists-file"), URL("storage://host/path/to/file.txt")
            )


async def test_storage_upload_dir_doesnt_exist(make_client: _MakeClient) -> None:
    async with make_client("https://example.com") as client:
        with pytest.raises(IsADirectoryError):
            await client.storage.upload_file(
                URL(FOLDER.as_uri()), URL("storage://host/path/to")
            )


async def test_storage_upload_not_a_file(make_client: _MakeClient) -> None:
    async with make_client("https://example.com") as client:
        with pytest.raises(OSError):
            await client.storage.upload_file(
                URL("file:///dev/random"), URL("storage://host/path/to")
            )


async def test_storage_upload_regular_file_to_existing_file_target(
    storage_server: Any, make_client: _MakeClient, storage_path: Path
) -> None:
    file_path = DATA_FOLDER / "file.txt"
    file_size = file_path.stat().st_size
    target_path = storage_path / "file.txt"
    progress = mock.Mock()

    async with make_client(storage_server.make_url("/")) as client:
        await client.storage.upload_file(
            URL(file_path.as_uri()), URL("storage:file.txt"), progress=progress
        )

    expected = file_path.read_bytes()
    uploaded = target_path.read_bytes()
    assert uploaded == expected

    progress.start.assert_called_with(str(file_path), file_size)
    progress.progress.assert_called_with(str(file_path), file_size)
    progress.complete.assert_called_with(str(file_path))


async def test_storage_upload_regular_file_to_existing_dir(
    storage_server: Any, make_client: _MakeClient, storage_path: Path
) -> None:
    file_path = DATA_FOLDER / "file.txt"
    folder = storage_path / "folder"
    folder.mkdir()
    target_path = folder / "file.txt"

    async with make_client(storage_server.make_url("/")) as client:
        await client.storage.upload_file(URL(file_path.as_uri()), URL("storage:folder"))

    expected = file_path.read_bytes()
    uploaded = target_path.read_bytes()
    assert uploaded == expected


async def test_storage_upload_regular_file_to_existing_file(
    storage_server: Any, make_client: _MakeClient, storage_path: Path
) -> None:
    file_path = DATA_FOLDER / "file.txt"
    folder = storage_path / "folder"
    folder.mkdir()
    target_path = folder / "file.txt"
    target_path.write_bytes(b"existing file")

    async with make_client(storage_server.make_url("/")) as client:
        await client.storage.upload_file(
            URL(file_path.as_uri()), URL("storage:folder/file.txt")
        )

    expected = file_path.read_bytes()
    uploaded = target_path.read_bytes()
    assert uploaded == expected


async def test_storage_upload_regular_file_to_existing_dir_with_trailing_slash(
    storage_server: Any, make_client: _MakeClient, storage_path: Path
) -> None:
    file_path = DATA_FOLDER / "file.txt"
    folder = storage_path / "folder"
    folder.mkdir()
    target_path = folder / "file.txt"

    async with make_client(storage_server.make_url("/")) as client:
        await client.storage.upload_file(
            URL(file_path.as_uri()), URL("storage:folder/")
        )

    expected = file_path.read_bytes()
    uploaded = target_path.read_bytes()
    assert uploaded == expected


async def test_storage_upload_regular_file_to_existing_non_dir(
    storage_server: Any, make_client: _MakeClient, storage_path: Path
) -> None:
    file_path = DATA_FOLDER / "file.txt"
    path = storage_path / "file"
    path.write_bytes(b"dummy")

    async with make_client(storage_server.make_url("/")) as client:
        with pytest.raises(NotADirectoryError):
            await client.storage.upload_file(
                URL(file_path.as_uri()), URL("storage:file/subfile.txt")
            )


async def test_storage_upload_regular_file_to_not_existing(
    storage_server: Any, make_client: _MakeClient
) -> None:
    file_path = DATA_FOLDER / "file.txt"

    async with make_client(storage_server.make_url("/")) as client:
        with pytest.raises(NotADirectoryError):
            await client.storage.upload_file(
                URL(file_path.as_uri()), URL("storage:absent-dir/absent-file.txt")
            )


async def test_storage_upload_recursive_src_doesnt_exist(
    make_client: _MakeClient
) -> None:
    async with make_client("https://example.com") as client:
        with pytest.raises(FileNotFoundError):
            await client.storage.upload_dir(
                URL("file:does_not_exist"), URL("storage://host/path/to")
            )


async def test_storage_upload_recursive_src_is_a_file(make_client: _MakeClient) -> None:
    file_path = DATA_FOLDER / "file.txt"

    async with make_client("https://example.com") as client:
        with pytest.raises(NotADirectoryError):
            await client.storage.upload_dir(
                URL(file_path.as_uri()), URL("storage://host/path/to")
            )


async def test_storage_upload_recursive_target_is_a_file(
    storage_server: Any, make_client: _MakeClient, storage_path: Path
) -> None:
    target_file = storage_path / "file.txt"
    target_file.write_bytes(b"dummy")

    async with make_client(storage_server.make_url("/")) as client:
        with pytest.raises(NotADirectoryError):
            await client.storage.upload_dir(
                URL(DATA_FOLDER.as_uri()), URL("storage:file.txt")
            )


async def test_storage_upload_recursive_ok(
    storage_server: Any, make_client: _MakeClient, storage_path: Path
) -> None:
    target_dir = storage_path / "folder"
    target_dir.mkdir()

    async with make_client(storage_server.make_url("/")) as client:
        await client.storage.upload_dir(
            URL(DATA_FOLDER.as_uri()) / "nested", URL("storage:folder")
        )
    diff = dircmp(DATA_FOLDER / "nested", target_dir)  # type: ignore
    assert not calc_diff(diff)  # type: ignore


async def test_storage_upload_recursive_slash_ending(
    storage_server: Any, make_client: _MakeClient, storage_path: Path
) -> None:
    target_dir = storage_path / "folder"
    target_dir.mkdir()

    async with make_client(storage_server.make_url("/")) as client:
        await client.storage.upload_dir(
            URL(DATA_FOLDER.as_uri()) / "nested", URL("storage:folder/")
        )
    diff = dircmp(DATA_FOLDER / "nested", target_dir / "nested")  # type: ignore
    assert not calc_diff(diff)  # type: ignore


async def test_storage_download_regular_file_to_absent_file(
    storage_server: Any, make_client: _MakeClient, tmp_path: Path, storage_path: Path
) -> None:
    src_file = DATA_FOLDER / "file.txt"
    storage_file = storage_path / "file.txt"
    storage_file.write_bytes(src_file.read_bytes())
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    local_file = local_dir / "file.txt"
    progress = mock.Mock()

    async with make_client(storage_server.make_url("/")) as client:
        await client.storage.download_file(
            URL("storage:file.txt"), URL(local_file.as_uri()), progress=progress
        )

    expected = src_file.read_bytes()
    downloaded = local_file.read_bytes()
    assert downloaded == expected

    file_name = local_file.as_uri()
    file_size = src_file.stat().st_size
    progress.start.assert_called_with(file_name, 0)
    progress.progress.assert_called_with(file_name, file_size)
    progress.complete.assert_called_with(file_name)


async def test_storage_download_regular_file_to_existing_file(
    storage_server: Any, make_client: _MakeClient, tmp_path: Path, storage_path: Path
) -> None:
    src_file = DATA_FOLDER / "file.txt"
    storage_file = storage_path / "file.txt"
    storage_file.write_bytes(src_file.read_bytes())
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    local_file = local_dir / "file.txt"
    local_file.write_bytes(b"Previous data")

    async with make_client(storage_server.make_url("/")) as client:
        await client.storage.download_file(
            URL("storage:file.txt"), URL(local_file.as_uri())
        )

    expected = src_file.read_bytes()
    downloaded = local_file.read_bytes()
    assert downloaded == expected


async def test_storage_download_regular_file_to_dir(
    storage_server: Any, make_client: _MakeClient, tmp_path: Path, storage_path: Path
) -> None:
    src_file = DATA_FOLDER / "file.txt"
    storage_file = storage_path / "file.txt"
    storage_file.write_bytes(src_file.read_bytes())
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    local_file = local_dir / "file.txt"

    async with make_client(storage_server.make_url("/")) as client:
        await client.storage.download_file(
            URL("storage:file.txt"), URL(local_dir.as_uri())
        )

    expected = src_file.read_bytes()
    downloaded = local_file.read_bytes()
    assert downloaded == expected


async def test_storage_download_regular_file_to_dir_slash_ended(
    storage_server: Any, make_client: _MakeClient, tmp_path: Path, storage_path: Path
) -> None:
    src_file = DATA_FOLDER / "file.txt"
    storage_file = storage_path / "file.txt"
    storage_file.write_bytes(src_file.read_bytes())
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    local_file = local_dir / "file.txt"

    async with make_client(storage_server.make_url("/")) as client:
        await client.storage.download_file(
            URL("storage:file.txt"), URL(local_dir.as_uri() + "/")
        )

    expected = src_file.read_bytes()
    downloaded = local_file.read_bytes()
    assert downloaded == expected


async def test_storage_download_regular_file_to_non_file(
    storage_server: Any, make_client: _MakeClient, tmp_path: Path, storage_path: Path
) -> None:
    src_file = DATA_FOLDER / "file.txt"
    storage_file = storage_path / "file.txt"
    storage_file.write_bytes(src_file.read_bytes())

    async with make_client(storage_server.make_url("/")) as client:
        with pytest.raises(OSError):
            await client.storage.download_file(
                URL("storage:file.txt"), URL("file:///dev/null")
            )


async def test_storage_download_dir(
    storage_server: Any, make_client: _MakeClient, tmp_path: Path, storage_path: Path
) -> None:
    storage_dir = storage_path / "folder"
    copytree(DATA_FOLDER / "nested", storage_dir)
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    target_dir = local_dir / "nested"

    async with make_client(storage_server.make_url("/")) as client:
        await client.storage.download_dir(
            URL("storage:folder"), URL(target_dir.as_uri())
        )

    diff = dircmp(DATA_FOLDER / "nested", target_dir)  # type: ignore
    assert not calc_diff(diff)  # type: ignore


async def test_storage_download_dir_slash_ending(
    storage_server: Any, make_client: _MakeClient, tmp_path: Path, storage_path: Path
) -> None:
    storage_dir = storage_path / "folder"
    copytree(DATA_FOLDER / "nested", storage_dir / "nested")
    local_dir = tmp_path / "local"
    local_dir.mkdir()

    async with make_client(storage_server.make_url("/")) as client:
        await client.storage.download_dir(
            URL("storage:folder"), URL(local_dir.as_uri() + "/")
        )

    diff = dircmp(DATA_FOLDER / "nested", local_dir / "nested")  # type: ignore
    assert not calc_diff(diff)  # type: ignore
