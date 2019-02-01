from pathlib import Path
from urllib.parse import urlparse

import pytest
from yarl import URL

from neuromation.cli.command_handlers import PlatformStorageOperation
from neuromation.cli.url_utils import local_path_to_url


class TestPathRendering:
    def test_principal_url_empty(self):
        operation = PlatformStorageOperation("researcher1")
        url = urlparse("storage:///")
        assert operation._get_principal(url) == "researcher1"

    def test_principal_url_path_only(self):
        operation = PlatformStorageOperation("researcher1")
        url = urlparse("storage:///data")
        assert operation._get_principal(url) == "researcher1"

    def test_principal_url_specified(self):
        operation = PlatformStorageOperation("researcher1")
        url = urlparse("storage://researcher2/")
        assert operation._get_principal(url) == "researcher2"

    def test_principal_url_specified_same(self):
        operation = PlatformStorageOperation("researcher1")
        url = urlparse("storage://researcher1/")
        assert operation._get_principal(url) == "researcher1"

    def test_principal_url_specified_tilde(self):
        operation = PlatformStorageOperation("researcher1")
        url = urlparse("storage://~/")
        assert operation._get_principal(url) == "researcher1"


class TestUrlUtils:
    _pwd = Path.cwd()

    @pytest.fixture
    def fake_homedir(self, monkeypatch):
        monkeypatch.setenv("HOME", "/home/user")

    def test_local_path_to_url__name(self):
        path = "file"
        url = local_path_to_url(path)
        assert url == URL(f"file://{self._pwd}/file")

    def test_local_path_to_url__dot_slash_name(self):
        path = "./file"
        url = local_path_to_url(path)
        assert url == URL(f"file://{self._pwd}/file")

    def test_local_path_to_url__relative_path(self):
        path = "d/e/file"
        url = local_path_to_url(path)
        assert url == URL(f"file://{self._pwd}/d/e/file")

    def test_local_path_to_url__dot_slash_relative_path(self):
        path = "./d/e/file"
        url = local_path_to_url(path)
        assert url == URL(f"file://{self._pwd}/d/e/file")

    def test_local_path_to_url__tilde_slash_name(self, fake_homedir):
        path = "~/file"
        url = local_path_to_url(path)
        assert url == URL(f"file:///home/user/file")

    def test_local_path_to_url__tilde_slash_relative_path(self, fake_homedir):
        path = "~/a/b/c/file"
        url = local_path_to_url(path)
        assert url == URL(f"file:///home/user/a/b/c/file")

    def test_local_path_to_url__absolute_path(self, fake_homedir):
        path = "/a/b/c/file"
        url = local_path_to_url(path)
        assert url == URL(f"file:///a/b/c/file")
