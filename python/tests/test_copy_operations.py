import pytest

from neuromation.cli.command_handlers import CopyOperation


def test_invalid_scheme_combinations():
    with pytest.raises(ValueError, match=r'schemes required'):
        CopyOperation.create('alice', 'file', 'file', False)

    with pytest.raises(ValueError, match=r'schemes required'):
        CopyOperation.create('alice', 'storage', 'storage', False)

    with pytest.raises(ValueError, match=r'schemes required'):
        CopyOperation.create('alice', 'storage', 'abrakadabra', False)

    with pytest.raises(ValueError, match=r'schemes required'):
        CopyOperation.create('alice', 'file', 'abrakadabra', False)

    with pytest.raises(ValueError, match=r'schemes required'):
        CopyOperation.create('alice', 'abrakadabra', 'abrakadabra', False)
