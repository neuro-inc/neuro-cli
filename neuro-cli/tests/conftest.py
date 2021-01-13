import asyncio
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import aiohttp
import aiohttp.pytest_plugin
import pytest
from jose import jwt
from yarl import URL

from neuro_sdk import Client, Cluster, Preset, __version__
from neuro_sdk.config import _AuthConfig, _AuthToken, _ConfigData, _save
from neuro_sdk.tracing import _make_trace_config

from neuro_cli.asyncio_utils import setup_child_watcher


def pytest_addoption(parser: Any, pluginmanager: Any) -> None:
    parser.addoption(
        "--rich-gen",
        default=False,
        action="store_true",
        help="Regenerate rich_cmp references from captured texts",
    )


setup_child_watcher()


def setup_test_loop(
    loop_factory: Callable[[], asyncio.AbstractEventLoop] = asyncio.new_event_loop
) -> asyncio.AbstractEventLoop:
    return loop_factory()


aiohttp.pytest_plugin.setup_test_loop = setup_test_loop


@pytest.fixture
def token() -> str:
    return jwt.encode({"identity": "user"}, "secret", algorithm="HS256")


@pytest.fixture
def auth_config() -> _AuthConfig:
    return _AuthConfig.create(
        auth_url=URL("https://dev-neuro.auth0.com/authorize"),
        token_url=URL("https://dev-neuro.auth0.com/oauth/token"),
        logout_url=URL("https://dev-neuro.auth0.com/v2/logout"),
        client_id="CLIENT-ID",
        audience="https://platform.dev.neu.ro",
        headless_callback_url=URL("https://https://dev.neu.ro/oauth/show-code"),
        success_redirect_url=URL("https://neu.ro/#running-your-first-job"),
        callback_urls=[
            URL("http://127.0.0.1:54540"),
            URL("http://127.0.0.1:54541"),
            URL("http://127.0.0.1:54542"),
        ],
    )


@pytest.fixture
def cluster_config() -> Cluster:
    return Cluster(
        registry_url=URL("https://registry-dev.neu.ro"),
        storage_url=URL("https://storage-dev.neu.ro"),
        blob_storage_url=URL("https://blob-storage-dev.neu.ro"),
        users_url=URL("https://users-dev.neu.ro"),
        monitoring_url=URL("https://monitoring-dev.neu.ro"),
        secrets_url=URL("https://secrets-dev.neu.ro"),
        disks_url=URL("https://disks-storage-dev.neu.ro"),
        presets={
            "gpu-small": Preset(
                cpu=7, memory_mb=30 * 1024, gpu=1, gpu_model="nvidia-tesla-k80"
            ),
            "gpu-large": Preset(
                cpu=7, memory_mb=60 * 1024, gpu=1, gpu_model="nvidia-tesla-v100"
            ),
            "cpu-small": Preset(cpu=7, memory_mb=2 * 1024),
            "cpu-large": Preset(cpu=7, memory_mb=14 * 1024),
            "cpu-large-p": Preset(
                cpu=7,
                memory_mb=14 * 1024,
                scheduler_enabled=True,
                preemptible_node=True,
            ),
        },
        name="default",
    )


@pytest.fixture
def make_client(
    token: str, auth_config: _AuthConfig, tmp_path: Path
) -> Callable[..., Client]:
    def go(
        url_str: str,
        *,
        registry_url: str = "https://registry-dev.neu.ro",
        trace_id: str = "bd7a977555f6b982",
        clusters: Optional[Dict[str, Cluster]] = None,
        token_url: Optional[URL] = None
    ) -> Client:
        url = URL(url_str)
        if clusters is None:
            cluster_config = Cluster(
                registry_url=URL(registry_url),
                monitoring_url=(url / "jobs"),
                storage_url=(url / "storage"),
                blob_storage_url=(url / "blob"),
                users_url=url,
                secrets_url=(url / "secrets"),
                disks_url=(url / "disks"),
                presets={
                    "gpu-small": Preset(
                        cpu=7, memory_mb=30 * 1024, gpu=1, gpu_model="nvidia-tesla-k80"
                    ),
                    "gpu-large": Preset(
                        cpu=7, memory_mb=60 * 1024, gpu=1, gpu_model="nvidia-tesla-v100"
                    ),
                    "cpu-small": Preset(cpu=7, memory_mb=2 * 1024),
                    "cpu-large": Preset(cpu=7, memory_mb=14 * 1024),
                },
                name="default",
            )
            clusters = {cluster_config.name: cluster_config}
        if token_url is not None:
            real_auth_config = replace(auth_config, token_url=token_url)
        else:
            real_auth_config = auth_config
        config = _ConfigData(
            auth_config=real_auth_config,
            auth_token=_AuthToken.create_non_expiring(token),
            url=URL(url),
            admin_url=URL(url) / ".." / ".." / "apis" / "admin" / "v1",
            version=__version__,
            cluster_name=next(iter(clusters)),
            clusters=clusters,
        )
        config_dir = tmp_path / ".neuro"
        _save(config, config_dir)
        session = aiohttp.ClientSession(trace_configs=[_make_trace_config()])
        return Client._create(session, config_dir, trace_id)

    return go
