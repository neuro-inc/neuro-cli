from io import BytesIO
from unittest import mock

import aiohttp
import pytest

from neuromation import client
from neuromation.client import (
    AuthenticationError,
    AuthorizationError,
    IllegalArgumentError,
    ResourceNotFound,
)
from utils import (
    BinaryResponse,
    JsonResponse,
    PlainResponse,
    mocked_async_context_manager,
)


@pytest.mark.asyncio
async def test_filenotfound_error(storage):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(
            JsonResponse(
                {"error": "blah!"},
                error=aiohttp.ClientResponseError(
                    request_info=None, history=None, status=404, message="ah!"
                ),
            )
        ),
    ):
        async with storage as s:
            with pytest.raises(ResourceNotFound):
                await s.rm(path="/file-not-exists.here")


@pytest.mark.asyncio
async def test_opem_notexists_file(storage):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(
            JsonResponse(
                {"error": "blah!"},
                error=aiohttp.ClientResponseError(
                    request_info=None, history=None, status=404, message="ah!"
                ),
            )
        ),
    ):
        async with storage as s:
            with pytest.raises(ResourceNotFound):
                async with s.open(path="/file-not-exists.here") as stream:
                    await stream.read()


@pytest.mark.asyncio
async def test_authorization_error(storage):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(
            JsonResponse(
                {"error": "blah!"},
                error=aiohttp.ClientResponseError(
                    request_info=None, history=None, status=403, message="ah!"
                ),
            )
        ),
    ):
        async with storage as s:
            with pytest.raises(AuthorizationError):
                await s.rm(path="/any.file")


@pytest.mark.asyncio
async def test_authentication_error(storage):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(
            JsonResponse(
                {"error": "blah!"},
                error=aiohttp.ClientResponseError(
                    request_info=None, history=None, status=401, message="ah!"
                ),
            )
        ),
    ):
        async with storage as s:
            with pytest.raises(AuthenticationError):
                await s.rm(path="/any.file")


@pytest.mark.asyncio
async def test_invalid_arguments_error(storage):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(
            JsonResponse(
                {"error": "blah!"},
                error=aiohttp.ClientResponseError(
                    request_info=None, history=None, status=400, message="ah!"
                ),
            )
        ),
    ):
        async with storage as s:
            with pytest.raises(IllegalArgumentError):
                await s.rm(path="")


@pytest.mark.asyncio
async def test_ls(storage):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(
            JsonResponse(
                {
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
            )
        ),
    ) as my_mock:
        async with storage as s:
            assert await s.ls(path="/home/dir") == [
                client.FileStatus(
                    path="foo",
                    size=1024,
                    type="FILE",
                    modification_time=0,
                    permission="read",
                ),
                client.FileStatus(
                    path="bar",
                    size=4 * 1024,
                    type="DIR",
                    modification_time=0,
                    permission="read",
                ),
            ]

        my_mock.assert_called_with(
            method="GET",
            url="http://127.0.0.1/storage/home/dir",
            params="LISTSTATUS",
            data=None,
            json=None,
        )


@pytest.mark.asyncio
async def test_stats(storage):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(
            JsonResponse(
                {
                    "FileStatus": {
                        "path": "/home/dir",
                        "length": 1024,
                        "modificationTime": 1540809272,
                        "permission": "read",
                        "type": "FILE",
                    }
                }
            )
        ),
    ) as my_mock:
        async with storage as s:
            assert await s.stats(path="/home/dir") == client.FileStatus(
                path="/home/dir",
                size=1024,
                type="FILE",
                modification_time=1540809272,
                permission="read",
            )

        my_mock.assert_called_with(
            method="GET",
            url="http://127.0.0.1/storage/home/dir",
            params="GETFILESTATUS",
            data=None,
            json=None,
        )


@pytest.mark.asyncio
async def test_mkdirs(storage):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(PlainResponse(text="")),
    ) as my_mock:
        async with storage as s:
            assert await s.mkdirs(path="/root/foo") == "/root/foo"
        my_mock.assert_called_with(
            method="PUT",
            json=None,
            url="http://127.0.0.1/storage/root/foo",
            params="MKDIRS",
            data=None,
        )


@pytest.mark.asyncio
async def test_rm(storage):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(PlainResponse(text="")),
    ) as my_mock:
        async with storage as s:
            assert await s.rm(path="foo")
        my_mock.assert_called_with(
            method="DELETE",
            json=None,
            url="http://127.0.0.1/storage/foo",
            params=None,
            data=None,
        )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(JsonResponse(json={})),
)
def test_mv(storage):
    assert storage.mv(src_path="foo", dst_path="bar")
    aiohttp.ClientSession.request.assert_called_with(
        method="POST",
        json=None,
        url="http://127.0.0.1/storage/foo",
        params={"op": "RENAME", "destination": "bar"},
        data=None,
    )


@pytest.mark.asyncio
async def test_create(storage):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(PlainResponse(text="")),
    ) as my_mock:
        data = BytesIO(b"bar")
        async with storage as s:
            assert await s.create(path="foo", data=data)
        my_mock.assert_called_with(
            method="PUT",
            url="http://127.0.0.1/storage/foo",
            params=None,
            data=data,
            json=None,
        )


@pytest.mark.asyncio
async def test_open(storage):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(BinaryResponse(data=b"bar")),
    ):
        async with storage as s:
            async with s.open(path="foo") as f:
                assert await f.read() == b"bar"
                aiohttp.ClientSession.request.assert_called_with(
                    method="GET",
                    url="http://127.0.0.1/storage/foo",
                    params=None,
                    json=None,
                    data=None,
                )
