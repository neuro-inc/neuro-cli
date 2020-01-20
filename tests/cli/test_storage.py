from pathlib import Path
from typing import Any, Callable

import toml

from neuromation.api import Client
from neuromation.cli.storage import calc_filters


_MakeClient = Callable[..., Client]


async def test_calc_filters_section_doesnt_exist(
    monkeypatch: Any, tmp_path: Path, make_client: _MakeClient
) -> None:

    async with make_client("https://example.com") as client:
        monkeypatch.chdir(tmp_path)
        local_conf = tmp_path / ".neuro.toml"
        # empty config
        local_conf.write_text("")
        assert await calc_filters(client, None) == ()


async def test_calc_filters_user_spec(
    monkeypatch: Any, tmp_path: Path, make_client: _MakeClient
) -> None:

    async with make_client("https://example.com") as client:
        monkeypatch.chdir(tmp_path)
        local_conf = tmp_path / ".neuro.toml"
        # empty config
        local_conf.write_text(
            toml.dumps({"storage": {"cp-exclude": ["*.jpg", "!main.jpg"]}})
        )
        assert await calc_filters(client, None) == (
            (True, "*.jpg"),
            (False, "main.jpg"),
        )
