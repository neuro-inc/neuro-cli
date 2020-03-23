from dataclasses import replace
from pathlib import Path
from typing import Callable, Dict, Optional

import aiohttp
import pytest
from jose import jwt
from yarl import URL

import neuromation
from neuromation.api import Client, Cluster, Preset
from neuromation.api.config import _AuthConfig, _AuthToken, _ConfigData, _save
from neuromation.api.tracing import _make_trace_config


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
def cluster_config() -> Cluster:
    return Cluster(
        registry_url=URL("https://registry-dev.neu.ro"),
        storage_url=URL("https://storage-dev.neu.ro"),
        users_url=URL("https://users-dev.neu.ro"),
        monitoring_url=URL("https://monitoring-dev.neu.ro"),
        presets={
            "gpu-small": Preset(
                cpu=7, memory_mb=30 * 1024, gpu=1, gpu_model="nvidia-tesla-k80"
            ),
            "gpu-large": Preset(
                cpu=7, memory_mb=60 * 1024, gpu=1, gpu_model="nvidia-tesla-v100"
            ),
            "cpu-small": Preset(cpu=7, memory_mb=2 * 1024),
            "cpu-large": Preset(cpu=7, memory_mb=14 * 1024),
            "cpu-large-p": Preset(cpu=7, memory_mb=14 * 1024, is_preemptible=True),
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
                users_url=url,
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
            version=neuromation.__version__,
            cluster_name=next(iter(clusters)),
            clusters=clusters,
        )
        config_dir = tmp_path / ".neuro"
        _save(config, config_dir)
        session = aiohttp.ClientSession(trace_configs=[_make_trace_config()])
        return Client._create(session, config_dir, trace_id)

    return go
