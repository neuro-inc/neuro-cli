from urllib.parse import urlparse

from neuromation.cli.command_handlers import PlatformStorageOperation


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
