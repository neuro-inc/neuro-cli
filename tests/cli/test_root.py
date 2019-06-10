import dataclasses

import aiohttp
import pytest

from neuromation.cli.root import Root, ConfigError


@pytest.fixture
def root_uninitialized():
    return Root(
        color=False,
        tty=False,
        terminal_size=(80, 25),
        disable_pypi_version_check=False,
        network_timeout=60,
        config_path="~/.nmrc",
    )


def test_auth_uninitialized(root_uninitialized):
    assert root_uninitialized.auth is None


def test_timeout(root_uninitialized):
    assert root_uninitialized.timeout == aiohttp.ClientTimeout(None, None, 60, 60)


def test_username_uninitialized(root_uninitialized):
    with pytest.raises(ConfigError):
        root_uninitialized.username


def test_url_uninitialized(root_uninitialized):
    with pytest.raises(ConfigError):
        root_uninitialized.url


def test_resource_presets_uninitialized(root_uninitialized):
    with pytest.raises(ConfigError):
        root_uninitialized.resource_presets


def test_get_session_cookie(root_uninitialized):
    assert root_uninitialized.get_session_cookie() is None
