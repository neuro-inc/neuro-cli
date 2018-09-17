import pytest

from neuromation.cli import rc
from neuromation.cli.rc import Config

DEFAULTS = rc.Config(
    url='http://platform.dev.neuromation.io/api/v1',
    auth=''
)


@pytest.fixture
def nmrc(tmpdir):
    return tmpdir.join('.nmrc')


def test_create(nmrc):
    conf = rc.create(nmrc, Config())
    assert conf == DEFAULTS
    assert nmrc.check()
    assert nmrc.read() == f'auth: \'\'\n' \
                          f'url: {DEFAULTS.url}\n'


def test_create_existing(nmrc):
    document = """
        url: 'http://a.b/c'
    """
    nmrc.write(document)

    with pytest.raises(FileExistsError):
        rc.create(nmrc, Config())

    assert nmrc.check()
    assert nmrc.read() == document


def test_load(nmrc):
    document = """
        url: 'http://a.b/c'
    """
    nmrc.write(document)

    config = rc.load(nmrc)
    assert config == rc.Config(url='http://a.b/c')


def test_load_missing(nmrc):
    config = rc.load(nmrc)
    assert nmrc.check()
    assert config == DEFAULTS
