from unittest import mock
from unittest.mock import patch

import aiohttp
import pytest

from neuromation.cli.command_handlers import PlatformSharingOperations
from tests.utils import PlainResponse, mocked_async_context_manager


@pytest.fixture()
def alice_sharing():
    return PlatformSharingOperations("alice")


@pytest.mark.asyncio
class TestNormalCases:
    async def test_alice_share_with_bob(
        self, alice_sharing, partial_mocked_resource_share
    ):
        partial_mocked_resource_share().patch("share", None)
        await alice_sharing.share(
            "storage:///some/data/belongs/to_both",
            "manage",
            "bob",
            partial_mocked_resource_share,
        )
        partial_mocked_resource_share().share.assert_called_once()
        partial_mocked_resource_share().share.assert_called_with(
            "storage://alice/some/data/belongs/to_both", "manage", "bob"
        )

    async def test_http_request(self, resource_sharing):
        with mock.patch(
            "aiohttp.ClientSession.request",
            new=mocked_async_context_manager(PlainResponse(text="")),
        ) as my_mock:
            resource_sharing.share(
                "storage://alice/some/data/belongs/to_both", "manage", "bob"
            )

            my_mock.assert_called_with(
                method="POST",
                url="http://127.0.0.1/users/bob/permissions",
                params=None,
                data=None,
                json=[
                    {
                        "uri": "storage://alice/some/data/belongs/to_both",
                        "action": "manage",
                    }
                ],
            )
