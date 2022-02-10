from yarl import URL

from neuro_cli.formatters.utils import uri_formatter


def test_uri_formatter_without_org() -> None:
    fmtr = uri_formatter(username="user", cluster_name="cluster", org_name=None)
    assert fmtr(URL("storage://cluster/user/path/to/file")) == "storage:path/to/file"
    assert fmtr(URL("storage://cluster/user/")) == "storage:"
    assert fmtr(URL("storage://cluster/user")) == "storage:"
    assert fmtr(URL("storage://cluster/")) == "storage:/"
    assert fmtr(URL("storage://cluster")) == "storage:/"
    assert (
        fmtr(URL("storage://cluster/otheruser/path/to/file"))
        == "storage:/otheruser/path/to/file"
    )
    assert (
        fmtr(URL("storage://cluster/org/user/path/to/file"))
        == "storage:/org/user/path/to/file"
    )
    assert (
        fmtr(URL("storage://othercluster/user/path/to/file"))
        == "storage://othercluster/user/path/to/file"
    )
    assert fmtr(URL("user://cluster/user/rest")) == "user://cluster/user/rest"


def test_uri_formatter_with_org() -> None:
    fmtr = uri_formatter(username="user", cluster_name="cluster", org_name="org")
    assert (
        fmtr(URL("storage://cluster/org/user/path/to/file")) == "storage:path/to/file"
    )
    assert fmtr(URL("storage://cluster/org/user/")) == "storage:"
    assert fmtr(URL("storage://cluster/org/user")) == "storage:"
    assert fmtr(URL("storage://cluster/org/")) == "storage:/"
    assert fmtr(URL("storage://cluster/org")) == "storage:/"
    assert fmtr(URL("storage://cluster/")) == "storage://cluster/"
    assert fmtr(URL("storage://cluster")) == "storage://cluster"
    assert (
        fmtr(URL("storage://cluster/user/path/to/file"))
        == "storage://cluster/user/path/to/file"
    )
    assert (
        fmtr(URL("storage://cluster/org/otheruser/path/to/file"))
        == "storage:/otheruser/path/to/file"
    )
    assert (
        fmtr(URL("storage://cluster/otherorg/user/path/to/file"))
        == "storage://cluster/otherorg/user/path/to/file"
    )
    assert (
        fmtr(URL("storage://othercluster/org/user/path/to/file"))
        == "storage://othercluster/org/user/path/to/file"
    )
    assert (
        fmtr(URL("storage://cluster/user/path/to/file"))
        == "storage://cluster/user/path/to/file"
    )
    assert fmtr(URL("user://cluster/org/user/rest")) == "user://cluster/org/user/rest"


def test_uri_formatter_special_chars_without_org() -> None:
    fmtr = uri_formatter(username="user", cluster_name="cluster", org_name=None)
    assert (
        fmtr(URL("storage://cluster/user/путь/к/файлу"))
        == "storage:%D0%BF%D1%83%D1%82%D1%8C/%D0%BA/%D1%84%D0%B0%D0%B9%D0%BB%D1%83"
    )
    assert (
        fmtr(URL("storage://cluster/otheruser/путь/к/файлу")) == "storage:/otheruser/"
        "%D0%BF%D1%83%D1%82%D1%8C/%D0%BA/%D1%84%D0%B0%D0%B9%D0%BB%D1%83"
    )
    assert (
        fmtr(URL("storage://othercluster/user/путь/к/файлу"))
        == "storage://othercluster/user/"
        "%D0%BF%D1%83%D1%82%D1%8C/%D0%BA/%D1%84%D0%B0%D0%B9%D0%BB%D1%83"
    )
    assert fmtr(URL("storage://cluster/user/%2525%3f%23")) == "storage:%2525%3F%23"
    assert (
        fmtr(URL("storage://cluster/otheruser/%2525%3f%23"))
        == "storage:/otheruser/%2525%3F%23"
    )
    assert (
        fmtr(URL("storage://othercluster/user/%2525%3f%23"))
        == "storage://othercluster/user/%2525%3F%23"
    )


def test_uri_formatter_special_chars_with_org() -> None:
    fmtr = uri_formatter(username="user", cluster_name="cluster", org_name="org")
    assert (
        fmtr(URL("storage://cluster/org/user/путь/к/файлу"))
        == "storage:%D0%BF%D1%83%D1%82%D1%8C/%D0%BA/%D1%84%D0%B0%D0%B9%D0%BB%D1%83"
    )
    assert (
        fmtr(URL("storage://cluster/org/otheruser/путь/к/файлу"))
        == "storage:/otheruser/"
        "%D0%BF%D1%83%D1%82%D1%8C/%D0%BA/%D1%84%D0%B0%D0%B9%D0%BB%D1%83"
    )
    assert (
        fmtr(URL("storage://othercluster/org/user/путь/к/файлу"))
        == "storage://othercluster/org/user/"
        "%D0%BF%D1%83%D1%82%D1%8C/%D0%BA/%D1%84%D0%B0%D0%B9%D0%BB%D1%83"
    )
    assert fmtr(URL("storage://cluster/org/user/%2525%3f%23")) == "storage:%2525%3F%23"
    assert (
        fmtr(URL("storage://cluster/org/otheruser/%2525%3f%23"))
        == "storage:/otheruser/%2525%3F%23"
    )
    assert (
        fmtr(URL("storage://othercluster/org/user/%2525%3f%23"))
        == "storage://othercluster/org/user/%2525%3F%23"
    )
