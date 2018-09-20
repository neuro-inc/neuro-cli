import pytest

from neuromation.cli.command_handlers import CopyOperation


def test_invalid_scheme_combinario():
    with pytest.raises(ValueError, match=r'schemes required'):
        CopyOperation.create('file', 'file', False)

    with pytest.raises(ValueError, match=r'schemes required'):
        CopyOperation.create('storage', 'storage', False)

    with pytest.raises(ValueError, match=r'schemes required'):
        CopyOperation.create('storage', 'abrakadabra', False)

    with pytest.raises(ValueError, match=r'schemes required'):
        CopyOperation.create('file', 'abrakadabra', False)

    with pytest.raises(ValueError, match=r'schemes required'):
        CopyOperation.create('abrakadabra', 'abrakadabra', False)
