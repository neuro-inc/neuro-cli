from pathlib import Path
from typing import Any, Callable

import toml

from neuro_sdk import Client

from neuro_cli.storage import calc_filters, calc_ignore_file_names

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
        local_conf.write_text(
            toml.dumps({"storage": {"cp-exclude": ["*.jpg", "!main.jpg"]}})
        )
        assert await calc_filters(client, None) == (
            (True, "*.jpg"),
            (False, "main.jpg"),
        )


async def test_calc_filters_user_spec_and_options(
    monkeypatch: Any, tmp_path: Path, make_client: _MakeClient
) -> None:

    async with make_client("https://example.com") as client:
        monkeypatch.chdir(tmp_path)
        local_conf = tmp_path / ".neuro.toml"
        local_conf.write_text(
            toml.dumps({"storage": {"cp-exclude": ["*.jpg", "!main.jpg"]}})
        )
        filters = ((False, "a*.jpg"), (True, "temp/"))
        assert await calc_filters(client, filters) == (
            (True, "*.jpg"),
            (False, "main.jpg"),
            (False, "a*.jpg"),
            (True, "temp/"),
        )


async def test_calc_ignore_file_names_default(
    monkeypatch: Any, tmp_path: Path, make_client: _MakeClient
) -> None:
    async with make_client("https://example.com") as client:
        monkeypatch.chdir(tmp_path)
        local_conf = tmp_path / ".neuro.toml"
        # empty config
        local_conf.write_text("")
        assert await calc_ignore_file_names(client, None) == [".neuroignore"]
        local_conf.write_text(toml.dumps({"storage": {}}))
        assert await calc_ignore_file_names(client, None) == [".neuroignore"]


async def test_calc_ignore_file_names_user_spec(
    monkeypatch: Any, tmp_path: Path, make_client: _MakeClient
) -> None:
    async with make_client("https://example.com") as client:
        monkeypatch.chdir(tmp_path)
        local_conf = tmp_path / ".neuro.toml"
        local_conf.write_text(
            toml.dumps(
                {"storage": {"cp-exclude-from-files": [".gitignore", ".hgignore"]}}
            )
        )
        assert await calc_ignore_file_names(client, None) == [".gitignore", ".hgignore"]
