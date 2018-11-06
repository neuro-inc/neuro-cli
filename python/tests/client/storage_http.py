from unittest.mock import patch

import aiohttp
import pytest

from neuromation.client import FileStatus, ResourceNotFound
from tests.utils import JsonResponse, mocked_async_context_manager


class TestStats:
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
    def test_non_existing_file(self, storage):
        with pytest.raises(ResourceNotFound):
            storage.stats(path="/file-not-exists.here")

    @patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(
            JsonResponse(
                {
                    "FileStatus": {
                        "size": 100,
                        "modificationTime": 1540809272,
                        "permission": "manage",
                        "type": "FILE",
                        "path": "existing.file",
                    }
                }
            )
        ),
    )
    def test_file_status(self, storage):
        file_stats = storage.stats(path="/existing.file")
        assert file_stats == FileStatus(
            path="existing.file",
            size=100,
            type="FILE",
            modificationTime=1540809272,
            permission="manage",
        )

    @patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(
            JsonResponse(
                {
                    "FileStatus": {
                        "size": 0,
                        "modificationTime": 1540809272,
                        "permission": "manage",
                        "type": "DIRECTORY",
                        "path": "existing.dir",
                    }
                }
            )
        ),
    )
    def test_dir_status(self, storage):
        file_stats = storage.stats(path="existing.dir")
        assert file_stats == FileStatus(
            path="existing.dir",
            size=0,
            type="DIRECTORY",
            modificationTime=1540809272,
            permission="manage",
        )
