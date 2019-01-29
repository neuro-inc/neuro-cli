from pathlib import Path
from textwrap import dedent

import pytest
from jose import jwt
from yarl import URL

from neuromation.cli import rc
from neuromation.cli.rc import AuthToken, Config
from neuromation.client.users import JWT_IDENTITY_CLAIM_OPTIONS


DEFAULTS = rc.Config(url="https://platform.dev.neuromation.io/api/v1")


@pytest.fixture
def nmrc(tmp_path):
    return tmp_path / ".nmrc"


@pytest.fixture
def patch_home_for_test(monkeypatch, nmrc):
    def home():
        return nmrc.parent

    monkeypatch.setattr(Path, "home", home)


def test_create(nmrc):
    conf = rc.create(nmrc, Config())
    assert conf == DEFAULTS
    assert nmrc.exists()
    expected_text = dedent(
        """\
    auth_config:
      audience: https://platform.dev.neuromation.io
      auth_url: https://dev-neuromation.auth0.com/authorize
      client_id: V7Jz87W9lhIlo0MyD0O6dufBvcXwM4DR
      success_redirect_url: https://platform.neuromation.io
      token_url: https://dev-neuromation.auth0.com/oauth/token
    github_rsa_path: ''
    url: https://platform.dev.neuromation.io/api/v1
    """
    )
    assert nmrc.read_text() == expected_text


@pytest.mark.usefixtures("patch_home_for_test")
class TestFactoryMethods:
    def test_factory(self):
        auth_token = AuthToken.create_non_expiring("token1")
        config: Config = Config(url="http://abc.def", auth_token=auth_token)
        rc.ConfigFactory._update_config(url="http://abc.def", auth_token=auth_token)
        config2: Config = rc.ConfigFactory.load()
        assert config == config2

    def test_factory_update_url(self):
        auth_token = AuthToken.create_non_expiring("token1")
        config: Config = Config(url="http://abc.def", auth_token=auth_token)
        rc.ConfigFactory.update_api_url(url="http://abc.def")
        config2: Config = rc.ConfigFactory.load()
        assert config.url == config2.url

    def test_factory_update_url_malformed(self):
        auth_token = AuthToken.create_non_expiring("token1")
        config: Config = Config(url="http://abc.def", auth_token=auth_token)
        with pytest.raises(ValueError):
            rc.ConfigFactory.update_api_url(url="ftp://abc.def")
        config2: Config = rc.ConfigFactory.load()
        assert config.url != config2.url

    def test_factory_update_url_malformed_trailing_slash(self):
        auth_token = AuthToken.create_non_expiring("token1")
        config: Config = Config(url="http://abc.def", auth_token=auth_token)
        with pytest.raises(ValueError):
            rc.ConfigFactory.update_api_url(url="http://abc.def/")
        config2: Config = rc.ConfigFactory.load()
        assert config.url != config2.url

    def test_factory_update_url_malformed_with_fragment(self):
        auth_token = AuthToken.create_non_expiring("token1")
        config: Config = Config(url="http://abc.def", auth_token=auth_token)
        with pytest.raises(ValueError):
            rc.ConfigFactory.update_api_url(url="http://abc.def?blabla")
        config2: Config = rc.ConfigFactory.load()
        assert config.url != config2.url

    def test_factory_update_url_malformed_with_anchor(self):
        auth_token = AuthToken.create_non_expiring("token1")
        config: Config = Config(url="http://abc.def", auth_token=auth_token)
        with pytest.raises(ValueError):
            rc.ConfigFactory.update_api_url(url="http://abc.def#ping")
        config2: Config = rc.ConfigFactory.load()
        assert config.url != config2.url

    def test_factory_update_id_rsa(self):
        config: Config = Config(
            url=DEFAULTS.url,
            auth_token=DEFAULTS.auth_token,
            github_rsa_path="~/.ssh/id_rsa",
        )
        rc.ConfigFactory.update_github_rsa_path("~/.ssh/id_rsa")
        config2: Config = rc.ConfigFactory.load()
        assert config == config2

    def test_factory_update_token_invalid(self):
        with pytest.raises(ValueError):
            rc.ConfigFactory.update_auth_token(token="not-a-token")

    def test_factory_update_token_no_identity(self):
        jwt_hdr = """eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"""
        jwt_claims = """eyJub3QtaWRlbnRpdHkiOiJub3QtaWRlbnRpdHkifQ"""
        jwt_sig = """ag9NbxxOvp2ufMCUXk2pU3MMf2zYftXHQdOZDJajlvE"""
        no_identity = f"{jwt_hdr}.{jwt_claims}.{jwt_sig}"
        with pytest.raises(ValueError):
            rc.ConfigFactory.update_auth_token(token=no_identity)

    def test_factory_forget_token(self, monkeypatch, nmrc):
        def home():
            return nmrc.parent

        monkeypatch.setattr(Path, "home", home)
        jwt_hdr = """eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"""
        jwt_claims = """eyJpZGVudGl0eSI6Im1lIn0"""
        jwt_sig = """mhRDoWlNw5J2cAU6LZCVlM20oRF64MtIfzquso2eAqU"""
        test_token = AuthToken.create_non_expiring(f"{jwt_hdr}.{jwt_claims}.{jwt_sig}")
        config: Config = Config(
            url=DEFAULTS.url,
            auth_token=test_token,
            github_rsa_path=DEFAULTS.github_rsa_path,
        )
        rc.ConfigFactory.update_auth_token(test_token.token)
        config2: Config = rc.ConfigFactory.load()
        assert config == config2
        rc.ConfigFactory.forget_auth_token()
        config3: Config = rc.ConfigFactory.load()
        default_config: config = Config()
        assert config3 == default_config


def test_docker_url():
    assert DEFAULTS.docker_registry_url() == URL("https://registry.dev.neuromation.io")
    custom_staging = rc.Config(url="https://platform.staging.neuromation.io/api/v1")
    url = custom_staging.docker_registry_url()
    assert url == URL("https://registry.staging.neuromation.io")

    prod = rc.Config(url="https://platform.neuromation.io/api/v1")
    url = prod.docker_registry_url()
    assert url == URL("https://registry.neuromation.io")


@pytest.mark.parametrize("identity_claim", JWT_IDENTITY_CLAIM_OPTIONS)
def test_jwt_user(identity_claim):
    assert DEFAULTS.get_platform_user_name() is None
    custom_staging = rc.Config(
        url="http://platform.staging.neuromation.io/api/v1",
        auth_token=AuthToken.create_non_expiring(
            jwt.encode({identity_claim: "testuser"}, "secret", algorithm="HS256")
        ),
    )
    user = custom_staging.get_platform_user_name()
    assert user == "testuser"


def test_jwt_user_missing():
    assert DEFAULTS.get_platform_user_name() is None
    custom_staging = rc.Config(
        url="http://platform.staging.neuromation.io/api/v1",
        auth_token=AuthToken.create_non_expiring(
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzcyI6InJhZmEifQ."
            "9JsoI-AkyDRbLbp4V00_z-K5cpgfZABU2L0z-NZ77oc"
        ),
    )
    with pytest.raises(ValueError, match="JWT Claims structure is not correct."):
        custom_staging.get_platform_user_name()


def test_create_existing(nmrc):
    document = """
        url: 'http://a.b/c'
    """
    nmrc.write_text(document)
    nmrc.chmod(0o600)

    with pytest.raises(FileExistsError):
        rc.create(nmrc, Config())

    assert nmrc.exists()
    assert nmrc.read_text() == document


def test_load(nmrc):
    document = """
        url: 'http://a.b/c'
    """
    nmrc.write_text(document)
    nmrc.chmod(0o600)

    config = rc.load(nmrc)
    assert config == rc.Config(url="http://a.b/c")


def test_load_missing(nmrc):
    config = rc.load(nmrc)
    assert nmrc.exists()
    assert config == DEFAULTS


def test_load_bad_file_mode(nmrc):
    document = """
        url: 'http://a.b/c'
    """
    nmrc.write_text(document)  # 0o644 by defaul

    with pytest.raises(rc.RCException):
        rc.load(nmrc)


def test_unregistered():
    config = rc.Config()
    with pytest.raises(rc.RCException):
        config._check_registered()
