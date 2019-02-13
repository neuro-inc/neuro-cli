import logging
from pathlib import Path
from textwrap import dedent
from unittest import mock

import pkg_resources
import pytest
from jose import jwt
from yarl import URL

from neuromation.cli import rc
from neuromation.cli.login import AuthConfig
from neuromation.cli.rc import AuthToken, Config
from neuromation.client.users import JWT_IDENTITY_CLAIM_OPTIONS


DEFAULTS = rc.Config(url="https://dev.ai.neuromation.io/api/v1")


@pytest.fixture
def nmrc(tmp_path):
    return tmp_path / ".nmrc"


@pytest.fixture
def patch_home_for_test(monkeypatch, nmrc):
    def home():
        return nmrc.parent

    monkeypatch.setattr(Path, "home", home)


def test_create__with_defaults(nmrc):
    conf = rc.create(nmrc, Config())
    assert conf == DEFAULTS
    assert nmrc.exists()
    expected_text = dedent(
        """\
    github_rsa_path: ''
    pypi:
      check_timestamp: 0
      pypi_version: 0.0.0
    url: https://dev.ai.neuromation.io/api/v1
    """
    )
    assert nmrc.read_text() == expected_text


def test_create__filled(nmrc):
    config = Config(
        url="https://dev.ai/api/v1",
        registry_url="https://registry-dev.ai/api/v1",
        auth_config=AuthConfig(
            auth_url=URL("url"),
            token_url=URL("url"),
            client_id="client_id",
            audience="audience",
            callback_urls=(URL("url1"), URL("url2")),
            success_redirect_url=URL("url"),
        ),
        auth_token=AuthToken(
            token="token", expiration_time=100_500, refresh_token="refresh_token"
        ),
    )
    created_config = rc.create(nmrc, config)
    assert created_config == config
    assert nmrc.exists()
    print(nmrc.read_text())
    expected_text = dedent(
        """\
    auth_config:
      audience: audience
      auth_url: url
      client_id: client_id
      success_redirect_url: url
      token_url: url
    auth_token:
      expiration_time: 100500
      refresh_token: refresh_token
      token: token
    github_rsa_path: ''
    pypi:
      check_timestamp: 0
      pypi_version: 0.0.0
    url: https://dev.ai/api/v1
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

    def test_factory_update_url_registry_url_updates_old_cnames(self):
        auth_token = AuthToken.create_non_expiring("token1")
        config: Config = Config(
            url="http://dev.platform.neuromation.io/api/v1", auth_token=auth_token
        )
        rc.ConfigFactory.update_api_url(
            url="http://staging.platform.neuromation.io/api/v1"
        )
        config2: Config = rc.ConfigFactory.load()
        assert config.url == "http://dev.platform.neuromation.io/api/v1"
        assert config.registry_url == "http://dev.registry.neuromation.io"
        assert config2.url == "http://staging.platform.neuromation.io/api/v1"
        assert config2.registry_url == "http://staging.registry.neuromation.io"

    def test_factory_update_url_registry_url_updates_new_cnames(self):
        auth_token = AuthToken.create_non_expiring("token1")
        config: Config = Config(
            url="https://dev.ai.neuromation.io/api/v1", auth_token=auth_token
        )
        rc.ConfigFactory.update_api_url(url="https://staging.ai.neuromation.io/api/v1")
        config2: Config = rc.ConfigFactory.load()
        assert config.url == "https://dev.ai.neuromation.io/api/v1"
        assert config.registry_url == "https://registry-dev.ai.neuromation.io"
        assert config2.url == "https://staging.ai.neuromation.io/api/v1"
        assert config2.registry_url == "https://registry-staging.ai.neuromation.io"

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

    def test_factory_update_url_and_auth_config(self):
        config = rc.ConfigFactory.load()
        assert config.url == "https://dev.ai.neuromation.io/api/v1"
        assert config.registry_url == "https://registry-dev.ai.neuromation.io"
        assert config.auth_config.auth_url == URL(
            "https://dev-neuromation.auth0.com/authorize"
        )

        rc.ConfigFactory.update_api_url(url="https://staging.ai.neuromation.io/api/v1")

        config = rc.ConfigFactory.load()
        assert config.url == "https://staging.ai.neuromation.io/api/v1"
        assert config.registry_url == "https://registry-staging.ai.neuromation.io"
        assert config.auth_config.auth_url == URL(
            "https://staging-neuromation.auth0.com/authorize"
        )

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

    def test_factory_update_last_checked_version(self):
        config = rc.ConfigFactory.load()
        assert config.pypi.pypi_version == pkg_resources.parse_version("0.0.0")
        newer_version = pkg_resources.parse_version("1.2.3b4")
        rc.ConfigFactory.update_last_checked_version(newer_version, 1234)
        config2 = rc.ConfigFactory.load()
        assert config2.pypi.pypi_version == newer_version
        assert config2.pypi.check_timestamp == 1234

    def test_factory_forget_token(self, monkeypatch, nmrc):
        def home():
            return nmrc.parent

        monkeypatch.setattr(Path, "home", home)
        jwt_hdr = """eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"""
        jwt_claims = """eyJpZGVudGl0eSI6Im1lIn0"""
        jwt_sig = """mhRDoWlNw5J2cAU6LZCVlM20oRF64MtIfzquso2eAqU"""
        token = f"{jwt_hdr}.{jwt_claims}.{jwt_sig}"

        rc.ConfigFactory.update_auth_token(token)
        expected_config = Config(
            url=DEFAULTS.url,
            auth_token=AuthToken(
                token=token, expiration_time=mock.ANY, refresh_token=""
            ),
            github_rsa_path=DEFAULTS.github_rsa_path,
        )
        config: Config = rc.ConfigFactory.load()
        assert config == expected_config

        rc.ConfigFactory.forget_auth_token()
        config3: Config = rc.ConfigFactory.load()
        default_config: Config = Config()
        assert config3 == default_config


def test_docker_url():
    assert DEFAULTS.registry_url == "https://registry-dev.ai.neuromation.io"
    custom_staging = rc.Config(url="https://staging.io.neuromation.io/api/v1")
    assert custom_staging.registry_url == "https://staging.io.neuromation.io"

    prod = rc.Config(url="https://platform.neuromation.io/api/v1")
    assert prod.registry_url == "https://registry.neuromation.io"


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
        registry_url: 'http://registry.a.b/c'
    """
    nmrc.write_text(document)
    nmrc.chmod(0o600)

    config = rc.load(nmrc)
    assert config == rc.Config(url="http://a.b/c", registry_url="http://registry.a.b/c")


def test_load_missing(nmrc):
    config = rc.load(nmrc)
    assert nmrc.exists()
    assert config == DEFAULTS


def test_load_bad_file_mode(nmrc):
    document = """
        url: 'http://a.b/c'
    """
    nmrc.write_text(document)  # 0o644 by default

    with pytest.raises(rc.RCException):
        rc.load(nmrc)


def test_unregistered():
    config = rc.Config()
    with pytest.raises(rc.RCException):
        config._check_registered()


def test_warn_in_has_newer_version_no_upgrade(caplog):
    config = rc.Config()
    with caplog.at_level(logging.WARNING):
        config.pypi.warn_if_has_newer_version()
    assert not caplog.records


def test_warn_in_has_newer_version_need_upgrade(caplog):
    config = rc.Config()
    config.pypi.pypi_version = pkg_resources.parse_version("100.500")
    with caplog.at_level(logging.WARNING):
        config.pypi.warn_if_has_newer_version()
    assert " version 100.500 is available." in caplog.records[0].message
