from unittest.mock import patch

import aiohttp
import pytest

from neuromation.cli.command_handlers import PlatformSharingOperations
from tests.utils import PlainResponse, mocked_async_context_manager


@pytest.fixture()
def alice_sharing():
    return PlatformSharingOperations("alice")


class TestNormalCases:
    def test_alice_share_with_bob(self, alice_sharing, partial_mocked_resource_share):
        alice_sharing.share(
            "storage:///some/data/belongs/to_both",
            "manage",
            "bob",
            partial_mocked_resource_share,
        )

        partial_mocked_resource_share().share.assert_called_once()
        partial_mocked_resource_share().share.assert_called_with(
            "storage://alice/some/data/belongs/to_both", "manage", "bob"
        )

    @patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(PlainResponse(text="")),
    )
    def test_http_request(self, resource_sharing):
        resource_sharing.share(
            "storage://alice/some/data/belongs/to_both", "manage", "bob"
        )

        aiohttp.ClientSession.request.assert_called_with(
            method="POST",
            url="http://127.0.0.1/users/bob/permissions",
            params=None,
            data=None,
            json=[
                {"uri": "storage://alice/some/data/belongs/to_both", "action": "manage"}
            ],
        )
