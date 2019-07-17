from typing import Callable

import aiohttp
import pkg_resources
import pytest
from jose import jwt
from yarl import URL

import neuromation
from neuromation.api import Client
from neuromation.api.config import (
    _AuthConfig,
    _AuthToken,
    _Config,
    _CookieSession,
    _PyPIVersion,
)
from neuromation.api.login import RunPreset, _ClusterConfig


@pytest.fixture
def token() -> str:
    return jwt.encode({"identity": "user"}, "secret", algorithm="HS256")


@pytest.fixture
def auth_config() -> _AuthConfig:
    return _AuthConfig.create(
        auth_url=URL("https://dev-neuromation.auth0.com/authorize"),
        token_url=URL("https://dev-neuromation.auth0.com/oauth/token"),
        client_id="CLIENT-ID",
        audience="https://platform.dev.neuromation.io",
        headless_callback_url=URL("https://https://dev.neu.ro/oauth/show-code"),
        success_redirect_url=URL("https://neu.ro/#running-your-first-job"),
        callback_urls=[
            URL("http://127.0.0.1:54540"),
            URL("http://127.0.0.1:54541"),
            URL("http://127.0.0.1:54542"),
        ],
    )


@pytest.fixture
def cluster_config() -> _ClusterConfig:
    return _ClusterConfig.create(
        registry_url=URL("https://registry-dev.neu.ro"),
        storage_url=URL("https://storage-dev.neu.ro"),
        users_url=URL("https://users-dev.neu.ro"),
        monitoring_url=URL("https://monitoring-dev.neu.ro"),
        resource_presets={
            "gpu-small": RunPreset(
                cpu=7, memory_mb=30 * 1024, gpu=1, gpu_model="nvidia-tesla-k80"
            ),
            "gpu-large": RunPreset(
                cpu=7, memory_mb=60 * 1024, gpu=1, gpu_model="nvidia-tesla-v100"
            ),
            "cpu-small": RunPreset(cpu=7, memory_mb=2 * 1024),
            "cpu-large": RunPreset(cpu=7, memory_mb=14 * 1024),
        },
    )


@pytest.fixture
def make_client(token: str, auth_config: _AuthConfig) -> Callable[..., Client]:
    def go(url_str: str, registry_url: str = "https://registry-dev.neu.ro") -> Client:
        url = URL(url_str)
        cluster_config = _ClusterConfig(
            registry_url=URL(registry_url),
            monitoring_url=(url / "jobs"),
            storage_url=(url / "storage"),
            users_url=url,
            resource_presets={
                "gpu-small": RunPreset(
                    cpu=7, memory_mb=30 * 1024, gpu=1, gpu_model="nvidia-tesla-k80"
                ),
                "gpu-large": RunPreset(
                    cpu=7, memory_mb=60 * 1024, gpu=1, gpu_model="nvidia-tesla-v100"
                ),
                "cpu-small": RunPreset(cpu=7, memory_mb=2 * 1024),
                "cpu-large": RunPreset(cpu=7, memory_mb=14 * 1024),
            },
        )
        config = _Config(
            auth_config=auth_config,
            auth_token=_AuthToken.create_non_expiring(token),
            pypi=_PyPIVersion.create_uninitialized(),
            url=URL(url),
            cluster_config=cluster_config,
            cookie_session=_CookieSession.create_uninitialized(),
            version=pkg_resources.parse_version(neuromation.__version__),
        )
        connector = aiohttp.TCPConnector()
        return Client._create(connector, config)

    return go
