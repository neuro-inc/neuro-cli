from pathlib import Path

import pytest

from neuromation.cli import rc
from neuromation.cli.rc import Config, ConfigFactory


DEFAULTS = rc.Config(url="https://platform.dev.neuromation.io/api/v1")


@pytest.fixture
def nmrc(tmp_path, setup_local_keyring):
    return tmp_path / ".nmrc"


@pytest.fixture
def setup_failed_keyring():
    import keyring
    import keyring.backends
    import keyring.backends.fail

    stored_keyring = keyring.get_keyring()
    keyring.set_keyring(keyring.backends.fail.Keyring())
    yield

    keyring.set_keyring(stored_keyring)


def test_create(nmrc):
    conf = rc.create(nmrc, Config())
    assert conf == DEFAULTS
    assert nmrc.exists()
    assert nmrc.read_text() == f"github_rsa_path: ''\n" f"url: {DEFAULTS.url}\n"


class TestFactoryMethods:
    @pytest.fixture
    def patch_home_for_test(self, monkeypatch, nmrc):
        def home():
            return nmrc.parent

        monkeypatch.setattr(Path, "home", home)

    def test_factory(self, patch_home_for_test):
        config: Config = Config(url="http://abc.def", auth="token1")
        rc.ConfigFactory._update_config(url="http://abc.def", auth="token1")
        config2: Config = rc.ConfigFactory.load()
        assert config == config2

    def test_factory_update_url(self, patch_home_for_test):
        config: Config = Config(url="http://abc.def", auth="token1")
        rc.ConfigFactory.update_api_url(url="http://abc.def")
        config2: Config = rc.ConfigFactory.load()
        assert config.url == config2.url

    def test_factory_update_url_malformed(self, patch_home_for_test):
        config: Config = Config(url="http://abc.def", auth="token1")
        with pytest.raises(ValueError):
            rc.ConfigFactory.update_api_url(url="ftp://abc.def")
        config2: Config = rc.ConfigFactory.load()
        assert config.url != config2.url

    def test_factory_update_url_malformed_trailing_slash(self, patch_home_for_test):
        config: Config = Config(url="http://abc.def", auth="token1")
        with pytest.raises(ValueError):
            rc.ConfigFactory.update_api_url(url="http://abc.def/")
        config2: Config = rc.ConfigFactory.load()
        assert config.url != config2.url

    def test_factory_update_url_malformed_with_fragment(self, patch_home_for_test):
        config: Config = Config(url="http://abc.def", auth="token1")
        with pytest.raises(ValueError):
            rc.ConfigFactory.update_api_url(url="http://abc.def?blabla")
        config2: Config = rc.ConfigFactory.load()
        assert config.url != config2.url

    def test_factory_update_url_malformed_with_anchor(self, patch_home_for_test):
        config: Config = Config(url="http://abc.def", auth="token1")
        with pytest.raises(ValueError):
            rc.ConfigFactory.update_api_url(url="http://abc.def#ping")
        config2: Config = rc.ConfigFactory.load()
        assert config.url != config2.url

    def test_factory_update_id_rsa(self, patch_home_for_test):
        config: Config = Config(
            url=DEFAULTS.url, auth=DEFAULTS.auth, github_rsa_path="~/.ssh/id_rsa"
        )
        rc.ConfigFactory.update_github_rsa_path("~/.ssh/id_rsa")
        config2: Config = rc.ConfigFactory.load()
        assert config == config2

    def test_factory_update_token_invalid(self, patch_home_for_test):
        with pytest.raises(ValueError):
            rc.ConfigFactory.update_auth_token(token="not-a-token")

    def test_factory_update_token_no_identity(self, patch_home_for_test):
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
        test_token = f"{jwt_hdr}.{jwt_claims}.{jwt_sig}"
        config: Config = Config(
            url=DEFAULTS.url, auth=test_token, github_rsa_path=DEFAULTS.github_rsa_path
        )
        rc.ConfigFactory.update_auth_token(test_token)
        config2: Config = rc.ConfigFactory.load()
        assert config == config2
        rc.ConfigFactory.forget_auth_token()
        config3: Config = rc.ConfigFactory.load()
        default_config: config = Config()
        assert config3 == default_config


def test_docker_url():
    assert DEFAULTS.docker_registry_url() == "registry.dev.neuromation.io"
    custom_staging = rc.Config(
        url="http://platform.staging.neuromation.io/api/v1", auth=""
    )
    url = custom_staging.docker_registry_url()
    assert url == "registry.staging.neuromation.io"

    prod = rc.Config(url="http://platform.neuromation.io/api/v1", auth="")
    url = prod.docker_registry_url()
    assert url == "registry.neuromation.io"


def test_jwt_user():
    assert DEFAULTS.get_platform_user_name() is None
    custom_staging = rc.Config(
        url="http://platform.staging.neuromation.io/api/v1",
        auth="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJpZGVudGl0eSI6InJhZmEifQ."
        "7-5YOshNXd6lKhQbMyglIQfUgBi9xNFW9vciBY9RSFA",
    )
    user = custom_staging.get_platform_user_name()
    assert user == "rafa"


def test_jwt_user_missing():
    assert DEFAULTS.get_platform_user_name() is None
    custom_staging = rc.Config(
        url="http://platform.staging.neuromation.io/api/v1",
        auth="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzcyI6InJhZmEifQ."
        "9JsoI-AkyDRbLbp4V00_z-K5cpgfZABU2L0z-NZ77oc",
    )
    user = custom_staging.get_platform_user_name()
    assert user is None


def test_create_existing(nmrc):
    document = """
        url: 'http://a.b/c'
    """
    nmrc.write_text(document)

    with pytest.raises(FileExistsError):
        rc.create(nmrc, Config())

    assert nmrc.exists()
    assert nmrc.read_text() == document


def test_load(nmrc):
    document = """
        url: 'http://a.b/c'
    """
    nmrc.write_text(document)

    config = rc.load(nmrc)
    assert config == rc.Config(url="http://a.b/c")


def test_merge_missing():
    conf: Config = Config(url="a", auth="b")
    merged = ConfigFactory.merge(conf, {})
    assert merged == Config(url="a", auth="b")


def test_merge_override_url():
    conf: Config = Config(url="a", auth="b")
    merged = ConfigFactory.merge(conf, {"url": "a1"})
    assert merged == Config(url="a1", auth="b")


def test_merge_override_token():
    conf: Config = Config(url="a", auth="b")
    merged = ConfigFactory.merge(conf, {"auth": "b1"})
    assert merged == Config(url="a", auth="b1")


def test_load_missing(nmrc):
    config = rc.load(nmrc)
    assert nmrc.exists()
    assert config == DEFAULTS


def test_keyring_fallbacks_to_nmrc(monkeypatch, nmrc, setup_failed_keyring):
    def home():
        return nmrc.parent

    monkeypatch.setattr(Path, "home", home)
    jwt_hdr = """eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"""
    jwt_claims = """eyJpZGVudGl0eSI6Im1lIn0"""
    jwt_sig = """mhRDoWlNw5J2cAU6LZCVlM20oRF64MtIfzquso2eAqU"""
    test_token = f"{jwt_hdr}.{jwt_claims}.{jwt_sig}"
    config: Config = Config(
        url=DEFAULTS.url, auth=test_token, github_rsa_path=DEFAULTS.github_rsa_path
    )
    rc.ConfigFactory.update_auth_token(test_token)
    assert (
        nmrc.read_text() == f"auth: {test_token}\n"
        f"github_rsa_path: '{DEFAULTS.github_rsa_path}'\n"
        f"url: {DEFAULTS.url}\n"
    )

    config2: Config = rc.ConfigFactory.load()
    assert config == config2

    rc.ConfigFactory.forget_auth_token()
    config3: Config = rc.ConfigFactory.load()

    assert (
        nmrc.read_text() == f"github_rsa_path: '{DEFAULTS.github_rsa_path}'\n"
        f"url: {DEFAULTS.url}\n"
    )

    default_config: config = Config()
    assert config3 == default_config
