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
        auth='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.'
             'eyJpZGVudGl0eSI6InJhZmEifQ.'
             '7-5YOshNXd6lKhQbMyglIQfUgBi9xNFW9vciBY9RSFA'
    )
    user = custom_staging.get_platform_user_name()
    assert user == 'rafa'


def test_jwt_user_missing():
    assert DEFAULTS.get_platform_user_name() is None
    custom_staging = rc.Config(
        url='http://platform.staging.neuromation.io/api/v1',
        auth='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.'
             'eyJzcyI6InJhZmEifQ.'
             '9JsoI-AkyDRbLbp4V00_z-K5cpgfZABU2L0z-NZ77oc'
    )
    user = custom_staging.get_platform_user_name()
    assert user is None


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
