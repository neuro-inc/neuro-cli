import pytest

from neuromation.cli.command_handlers import PlatformStorageShare


@pytest.fixture()
def alice_sharing():
    return PlatformStorageShare('alice')


class TestNormalCases:

    def test_alice_share_with_bob(self,
                                  alice_sharing,
                                  partial_mocked_resource_share):
        alice_sharing.share('storage:///some/data/belongs/to_both',
                            'manage', 'bob', partial_mocked_resource_share)

        partial_mocked_resource_share().share.assert_called_once()
        partial_mocked_resource_share().share.assert_called_with(
            'storage://alice/some/data/belongs/to_both',
            'manage',
            'bob'
        )
