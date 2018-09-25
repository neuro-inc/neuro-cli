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


def test_docker_url():
    assert DEFAULTS.docker_registry_url() == 'registry.dev.neuromation.io'
    custom_staging = rc.Config(
        url='http://platform.staging.neuromation.io/api/v1',
        auth=''
    )
    url = custom_staging.docker_registry_url()
    assert url == 'registry.staging.neuromation.io'

    prod = rc.Config(
        url='http://platform.neuromation.io/api/v1',
        auth=''
    )
    url = prod.docker_registry_url()
    assert url == 'registry.neuromation.io'


def test_jwt_user():
    assert DEFAULTS.get_platform_user_name() is None
    custom_staging = rc.Config(
        url='http://platform.staging.neuromation.io/api/v1',
        auth='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImlkZW50aXR5IjoicmF'
             'mYSJ9.eyJpZGVudGl0eSI6InJhZmEifQ.3ZVl8v2aMeeMTl57gTQn5K'
             'tQD5t4P0tOXyoM3J8kSqw'
    )
    user = custom_staging.get_platform_user_name()
    assert user == 'rafa'


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
