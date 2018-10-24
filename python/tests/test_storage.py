from io import BytesIO
from unittest.mock import patch

import aiohttp
import pytest
from utils import (
    BinaryResponse,
    JsonResponse,
    PlainResponse,
    mocked_async_context_manager,
)

from neuromation import client
from neuromation.client import (
    AuthenticationError,
    AuthorizationError,
    IllegalArgumentError,
    ResourceNotFound,
)


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {"error": "blah!"},
            error=aiohttp.ClientResponseError(
                request_info=None, history=None, status=404, message="ah!"
            ),
        )
    ),
)
def test_filenotfound_error(storage):
    with pytest.raises(ResourceNotFound):
        storage.rm(path="/file-not-exists.here")


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {"error": "blah!"},
            error=aiohttp.ClientResponseError(
                request_info=None, history=None, status=404, message="ah!"
            ),
        )
    ),
)
def test_opem_notexists_file(storage):
    with pytest.raises(ResourceNotFound):
        with storage.open(path="/file-not-exists.here") as stream:
            stream.read()


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {"error": "blah!"},
            error=aiohttp.ClientResponseError(
                request_info=None, history=None, status=403, message="ah!"
            ),
        )
    ),
)
def test_authorization_error(storage):
    with pytest.raises(AuthorizationError):
        storage.rm(path="/any.file")


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {"error": "blah!"},
            error=aiohttp.ClientResponseError(
                request_info=None, history=None, status=401, message="ah!"
            ),
        )
    ),
)
def test_authentication_error(storage):
    with pytest.raises(AuthenticationError):
        storage.rm(path="/any.file")


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {"error": "blah!"},
            error=aiohttp.ClientResponseError(
                request_info=None, history=None, status=400, message="ah!"
            ),
        )
    ),
)
def test_invalid_arguments_error(storage):
    with pytest.raises(IllegalArgumentError):
        storage.rm(path="")


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            [
                {"path": "foo", "size": 1024, "type": "FILE"},
                {"path": "bar", "size": 4 * 1024, "type": "DIR"},
            ]
        )
    ),
)
def test_ls(storage):
    assert storage.ls(path="/home/dir") == [
        client.FileStatus(path="foo", size=1024, type="FILE"),
        client.FileStatus(path="bar", size=4 * 1024, type="DIR"),
    ]

    aiohttp.ClientSession.request.assert_called_with(
        method="GET",
        url="http://127.0.0.1/storage/home/dir",
        params="LISTSTATUS",
        data=None,
        json=None,
    )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(PlainResponse(text="")),
)
def test_mkdirs(storage):
    assert storage.mkdirs(path="/root/foo") == "/root/foo"
    aiohttp.ClientSession.request.assert_called_with(
        method="PUT",
        json=None,
        url="http://127.0.0.1/storage/root/foo",
        params="MKDIRS",
        data=None,
    )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(PlainResponse(text="")),
)
def test_rm(storage):
    assert storage.rm(path="foo")
    aiohttp.ClientSession.request.assert_called_with(
        method="DELETE",
        json=None,
        url="http://127.0.0.1/storage/foo",
        params=None,
        data=None,
    )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(PlainResponse(text="")),
)
def test_create(storage):
    data = BytesIO(b"bar")
    assert storage.create(path="foo", data=data)
    aiohttp.ClientSession.request.assert_called_with(
        method="PUT",
        url="http://127.0.0.1/storage/foo",
        params=None,
        data=data,
        json=None,
    )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(BinaryResponse(data=b"bar")),
)
def test_open(storage):
    with storage.open(path="foo") as f:
        assert f.read() == b"bar"
        aiohttp.ClientSession.request.assert_called_with(
            method="GET",
            url="http://127.0.0.1/storage/foo",
            params=None,
            json=None,
            data=None,
        )
