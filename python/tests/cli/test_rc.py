import pytest

from neuromation.cli import rc

DEFAULTS = rc.Config(
    url='http://platform.dev.neuromation.io/api/v1',
    auth='Basic bm9ib2R5Om5vYm9keQ=='
)


@pytest.fixture
def nmrc(tmpdir):
    return tmpdir.join('.nmrc')


def test_create(nmrc):
    conf = rc.create(nmrc)
    assert conf == DEFAULTS
    assert nmrc.check()
    assert nmrc.read() == f'auth: Basic bm9ib2R5Om5vYm9keQ==\n' \
                          f'url: {DEFAULTS.url}\n'


def test_create_existing(nmrc):
    document = """
        url: 'http://a.b/c'
    """
    nmrc.write(document)

    with pytest.raises(FileExistsError):
        rc.create(nmrc)

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
