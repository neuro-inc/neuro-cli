from typing import Optional

import pytest
from yarl import URL

from neuro_cli.formatters.utils import uri_formatter


@pytest.mark.parametrize("scheme", ("storage", "image"))
def test_uri_formatter_without_org(scheme: str) -> None:
    fmtr = uri_formatter(username="user", cluster_name="cluster", org_name=None)
    assert (
        fmtr(URL(f"{scheme}://cluster/user/path/to/file")) == f"{scheme}:path/to/file"
    )
    assert fmtr(URL(f"{scheme}://cluster/user/")) == f"{scheme}:"
    assert fmtr(URL(f"{scheme}://cluster/user")) == f"{scheme}:"
    assert fmtr(URL(f"{scheme}://cluster/")) == f"{scheme}:/"
    assert fmtr(URL(f"{scheme}://cluster")) == f"{scheme}:/"
    assert (
        fmtr(URL(f"{scheme}://cluster/otheruser/path/to/file"))
        == f"{scheme}:/otheruser/path/to/file"
    )
    assert (
        fmtr(URL(f"{scheme}://cluster/org/user/path/to/file"))
        == f"{scheme}:/org/user/path/to/file"
    )
    assert (
        fmtr(URL(f"{scheme}://othercluster/user/path/to/file"))
        == f"{scheme}://othercluster/user/path/to/file"
    )
    assert fmtr(URL("user://cluster/user/rest")) == "user://cluster/user/rest"


@pytest.mark.parametrize("scheme", ("storage", "image"))
def test_uri_formatter_with_org(scheme: str) -> None:
    fmtr = uri_formatter(username="user", cluster_name="cluster", org_name="org")
    assert (
        fmtr(URL(f"{scheme}://cluster/org/user/path/to/file"))
        == f"{scheme}:path/to/file"
    )
    assert fmtr(URL(f"{scheme}://cluster/org/user/")) == f"{scheme}:"
    assert fmtr(URL(f"{scheme}://cluster/org/user")) == f"{scheme}:"
    assert fmtr(URL(f"{scheme}://cluster/org/")) == f"{scheme}:/"
    assert fmtr(URL(f"{scheme}://cluster/org")) == f"{scheme}:/"
    assert fmtr(URL(f"{scheme}://cluster/")) == f"{scheme}://cluster/"
    assert fmtr(URL(f"{scheme}://cluster")) == f"{scheme}://cluster"
    assert (
        fmtr(URL(f"{scheme}://cluster/user/path/to/file"))
        == f"{scheme}://cluster/user/path/to/file"
    )
    assert (
        fmtr(URL(f"{scheme}://cluster/org/otheruser/path/to/file"))
        == f"{scheme}:/otheruser/path/to/file"
    )
    assert (
        fmtr(URL(f"{scheme}://cluster/otherorg/user/path/to/file"))
        == f"{scheme}://cluster/otherorg/user/path/to/file"
    )
    assert (
        fmtr(URL(f"{scheme}://othercluster/org/user/path/to/file"))
        == f"{scheme}://othercluster/org/user/path/to/file"
    )
    assert (
        fmtr(URL(f"{scheme}://cluster/user/path/to/file"))
        == f"{scheme}://cluster/user/path/to/file"
    )
    assert fmtr(URL("user://cluster/org/user/rest")) == "user://cluster/org/user/rest"


@pytest.mark.parametrize("org_name", (None, "org"))
def test_global_uri_formatter(org_name: Optional[str]) -> None:
    fmtr = uri_formatter(username="user", cluster_name="cluster", org_name=org_name)
    assert fmtr(URL("user://cluster/user/rest")) == "user://cluster/user/rest"
    assert fmtr(URL("user://cluster/org/user/rest")) == "user://cluster/org/user/rest"


@pytest.mark.parametrize("scheme", ("storage", "image"))
def test_uri_formatter_special_chars_without_org(scheme: str) -> None:
    fmtr = uri_formatter(username="user", cluster_name="cluster", org_name=None)
    assert (
        fmtr(URL(f"{scheme}://cluster/user/путь/к/файлу"))
        == f"{scheme}:%D0%BF%D1%83%D1%82%D1%8C/%D0%BA/%D1%84%D0%B0%D0%B9%D0%BB%D1%83"
    )
    assert (
        fmtr(URL(f"{scheme}://cluster/otheruser/путь/к/файлу"))
        == f"{scheme}:/otheruser/"
        "%D0%BF%D1%83%D1%82%D1%8C/%D0%BA/%D1%84%D0%B0%D0%B9%D0%BB%D1%83"
    )
    assert (
        fmtr(URL(f"{scheme}://othercluster/user/путь/к/файлу"))
        == f"{scheme}://othercluster/user/"
        "%D0%BF%D1%83%D1%82%D1%8C/%D0%BA/%D1%84%D0%B0%D0%B9%D0%BB%D1%83"
    )
    assert fmtr(URL(f"{scheme}://cluster/user/%2525%3f%23")) == f"{scheme}:%2525%3F%23"
    assert (
        fmtr(URL(f"{scheme}://cluster/otheruser/%2525%3f%23"))
        == f"{scheme}:/otheruser/%2525%3F%23"
    )
    assert (
        fmtr(URL(f"{scheme}://othercluster/user/%2525%3f%23"))
        == f"{scheme}://othercluster/user/%2525%3F%23"
    )


@pytest.mark.parametrize("scheme", ("storage", "image"))
def test_uri_formatter_special_chars_with_org(scheme: str) -> None:
    fmtr = uri_formatter(username="user", cluster_name="cluster", org_name="org")
    assert (
        fmtr(URL(f"{scheme}://cluster/org/user/путь/к/файлу"))
        == f"{scheme}:%D0%BF%D1%83%D1%82%D1%8C/%D0%BA/%D1%84%D0%B0%D0%B9%D0%BB%D1%83"
    )
    assert (
        fmtr(URL(f"{scheme}://cluster/org/otheruser/путь/к/файлу"))
        == f"{scheme}:/otheruser/"
        "%D0%BF%D1%83%D1%82%D1%8C/%D0%BA/%D1%84%D0%B0%D0%B9%D0%BB%D1%83"
    )
    assert (
        fmtr(URL(f"{scheme}://othercluster/org/user/путь/к/файлу"))
        == f"{scheme}://othercluster/org/user/"
        "%D0%BF%D1%83%D1%82%D1%8C/%D0%BA/%D1%84%D0%B0%D0%B9%D0%BB%D1%83"
    )
    assert (
        fmtr(URL(f"{scheme}://cluster/org/user/%2525%3f%23")) == f"{scheme}:%2525%3F%23"
    )
    assert (
        fmtr(URL(f"{scheme}://cluster/org/otheruser/%2525%3f%23"))
        == f"{scheme}:/otheruser/%2525%3F%23"
    )
    assert (
        fmtr(URL(f"{scheme}://othercluster/org/user/%2525%3f%23"))
        == f"{scheme}://othercluster/org/user/%2525%3F%23"
    )
