import pytest
from yarl import URL

import neuromation
from neuromation.api import Preset
from neuromation.api.config import (
    _AuthConfig,
    _AuthToken,
    _ClusterConfig,
    _Config,
    _CookieSession,
    _PyPIVersion,
)


class TestConfig:
    def test_check_initialized(self) -> None:
        auth_config_good = _AuthConfig.create(
            auth_url=URL("auth_url"),
            token_url=URL("http://token"),
            client_id="client-id",
            audience="everyone",
            headless_callback_url=URL("https://dev.neu.ro/oauth/show-code"),
        )
        assert auth_config_good.is_initialized()

        cluster_config_good = _ClusterConfig.create(
            registry_url=URL("http://value"),
            storage_url=URL("http://value"),
            users_url=URL("http://value"),
            monitoring_url=URL("http://value"),
            resource_presets={"default": Preset(cpu=1, memory_mb=2 * 1024)},
        )
        assert cluster_config_good.is_initialized()

        config = _Config(
            auth_config=auth_config_good,
            auth_token=_AuthToken(
                token="token", expiration_time=10, refresh_token="ok"
            ),
            cluster_config=cluster_config_good,
            pypi=_PyPIVersion(
                pypi_version="1.2.3",
                check_timestamp=20,
                certifi_pypi_version="3.4.5",
                certifi_check_timestamp=40,
            ),
            url=URL("https://dev.neu.ro"),
            cookie_session=_CookieSession.create_uninitialized(),
            version=neuromation.__version__,
        )
        config.check_initialized()  # check no exceptions

    def test_check_initialized_bad_auth_config(self) -> None:
        auth_config_bad = _AuthConfig.create(
            auth_url=URL(),  # empty
            token_url=URL("http://token"),
            client_id="client-id",
            audience="everyone",
            headless_callback_url=URL("https://dev.neu.ro/oauth/show-code"),
        )
        assert not auth_config_bad.is_initialized()

        cluster_config_good = _ClusterConfig.create(
            registry_url=URL("http://value"),
            storage_url=URL("http://value"),
            users_url=URL("http://value"),
            monitoring_url=URL("http://value"),
            resource_presets={"default": Preset(cpu=1, memory_mb=2 * 1024)},
        )
        assert cluster_config_good.is_initialized()

        config = _Config(
            auth_config=auth_config_bad,
            auth_token=_AuthToken(
                token="token", expiration_time=10, refresh_token="ok"
            ),
            cluster_config=cluster_config_good,
            pypi=_PyPIVersion(
                pypi_version="1.2.3",
                check_timestamp=20,
                certifi_pypi_version="3.4.5",
                certifi_check_timestamp=40,
            ),
            url=URL("https://dev.neu.ro"),
            cookie_session=_CookieSession.create_uninitialized(),
            version=neuromation.__version__,
        )
        with pytest.raises(ValueError, match="Missing server configuration"):
            config.check_initialized()

    def test_check_initialized_bad_cluster_config(self) -> None:
        auth_config_bad = _AuthConfig.create(
            auth_url=URL("auth_url"),
            token_url=URL("http://token"),
            client_id="client-id",
            audience="everyone",
            headless_callback_url=URL("https://dev.neu.ro/oauth/show-code"),
        )
        assert auth_config_bad.is_initialized()

        cluster_config_good = _ClusterConfig.create(
            registry_url=URL(),  # empty
            storage_url=URL("http://value"),
            users_url=URL("http://value"),
            monitoring_url=URL("http://value"),
            resource_presets={"default": Preset(cpu=1, memory_mb=2 * 1024)},
        )
        assert not cluster_config_good.is_initialized()

        config = _Config(
            auth_config=auth_config_bad,
            auth_token=_AuthToken(
                token="token", expiration_time=10, refresh_token="ok"
            ),
            cluster_config=cluster_config_good,
            pypi=_PyPIVersion(
                pypi_version="1.2.3",
                check_timestamp=20,
                certifi_pypi_version="3.4.5",
                certifi_check_timestamp=40,
            ),
            url=URL("https://dev.neu.ro"),
            cookie_session=_CookieSession.create_uninitialized(),
            version=neuromation.__version__,
        )
        with pytest.raises(ValueError, match="Missing server configuration"):
            config.check_initialized()
