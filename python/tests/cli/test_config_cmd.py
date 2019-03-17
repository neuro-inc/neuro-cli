import json
import re
from pathlib import Path

from yarl import URL


class TestDocker:
    def test_path_not_exists(self, run_cli, tmp_path: Path):
        path = tmp_path / "some" / "not-exists"
        json_path = path / "config.json"
        capture = run_cli(["config", "docker", "--config", str(path)])
        assert not capture.err
        assert json_path.is_file()

    def test_path_is_not_dir(self, run_cli, tmp_path: Path):
        path = tmp_path / "file"
        with path.open("w") as file:
            file.write("text")
        captured = run_cli(["config", "docker", "--config", str(path)])
        assert re.match(r"Specified path is not a directory", captured.out)

    def test_new_file(self, run_cli, tmp_path: Path, config):
        path = tmp_path / ".docker"
        json_path = path / "config.json"
        capture = run_cli(["config", "docker", "--config", str(path)])
        assert not capture.err
        assert json_path.is_file()
        with json_path.open() as fp:
            payload = json.load(fp)
        registry = URL(config.registry_url).host
        assert payload["credHelpers"] == {registry: "neuro"}

    def test_merge_file_without_helpers(self, run_cli, tmp_path: Path, config):
        path = tmp_path / ".docker"
        path.mkdir()
        json_path = path / "config.json"
        with json_path.open("w") as fp:
            json.dump({"test": "value"}, fp)
        capture = run_cli(["config", "docker", "--config", str(path)])
        assert not capture.err
        assert json_path.is_file()
        with json_path.open() as fp:
            payload = json.load(fp)
        registry = URL(config.registry_url).host
        assert payload["credHelpers"] == {registry: "neuro"}
        assert payload["test"] == "value"

    def test_merge_file_without_helpers(self, run_cli, tmp_path: Path, config):
        path = tmp_path / ".docker"
        path.mkdir()
        json_path = path / "config.json"
        with json_path.open("w") as fp:
            json.dump({"test": "value", "credHelpers": {"some.com": "handler"}}, fp)
        capture = run_cli(["config", "docker", "--config", str(path)])
        assert not capture.err
        assert json_path.is_file()
        with json_path.open() as fp:
            payload = json.load(fp)
        registry = URL(config.registry_url).host
        assert payload["credHelpers"] == {registry: "neuro", "some.com": "handler"}
        assert payload["test"] == "value"
