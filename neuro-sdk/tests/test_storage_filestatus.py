from yarl import URL

from neuro_sdk import FileStatusType
from neuro_sdk.storage import _file_status_from_api_ls, _file_status_from_api_stat


def test_from_api() -> None:
    stat = _file_status_from_api_ls(
        URL("storage://default/user/foo"),
        {
            "path": "name",
            "type": "FILE",
            "length": 1234,
            "modificationTime": 3456,
            "permission": "read",
        },
    )
    assert stat.path == "name"
    assert stat.type == FileStatusType.FILE
    assert stat.size == 1234
    assert stat.modification_time == 3456
    assert stat.permission == "read"


def test_file() -> None:
    stat = _file_status_from_api_ls(
        URL("storage://default/user/foo"),
        {
            "path": "name",
            "type": "FILE",
            "length": 1234,
            "modificationTime": 3456,
            "permission": "read",
        },
    )
    assert stat.type == FileStatusType.FILE
    assert stat.is_file()
    assert not stat.is_dir()


def test_is_dir() -> None:
    stat = _file_status_from_api_ls(
        URL("storage://default/user/foo"),
        {
            "path": "name",
            "type": "DIRECTORY",
            "length": 1234,
            "modificationTime": 3456,
            "permission": "read",
        },
    )
    assert stat.type == FileStatusType.DIRECTORY
    assert not stat.is_file()
    assert stat.is_dir()


def test_name() -> None:
    stat = _file_status_from_api_ls(
        URL("storage://default/user/foo"),
        {
            "path": "name",
            "type": "FILE",
            "length": 1234,
            "modificationTime": 3456,
            "permission": "read",
        },
    )
    assert stat.name == "name"


def test_uri_ls() -> None:
    stat = _file_status_from_api_ls(
        URL("storage://default/user/foo"),
        {
            "path": "name",
            "type": "FILE",
            "length": 1234,
            "modificationTime": 3456,
            "permission": "read",
        },
    )
    assert stat.uri == URL("storage://default/user/foo/name")


def test_uri_stat() -> None:
    stat = _file_status_from_api_stat(
        "default",
        {
            "path": "/user/foo/name",
            "type": "FILE",
            "length": 1234,
            "modificationTime": 3456,
            "permission": "read",
        },
    )
    assert stat.uri == URL("storage://default/user/foo/name")


def test_uri_stat_user_home() -> None:
    stat = _file_status_from_api_stat(
        "default",
        {
            "path": "/user",
            "type": "FILE",
            "length": 1234,
            "modificationTime": 3456,
            "permission": "read",
        },
    )
    assert stat.uri == URL("storage://default/user")


def test_uri_stat_cluster_only() -> None:
    stat = _file_status_from_api_stat(
        "default",
        {
            "path": "/",
            "type": "FILE",
            "length": 1234,
            "modificationTime": 3456,
            "permission": "read",
        },
    )
    assert stat.uri == URL("storage://default/")


def test_uri_forbidden_symbols() -> None:
    stat = _file_status_from_api_stat(
        "default",
        {
            "path": "/user/path#%2d?:@~ßto",
            "type": "FILE",
            "length": 1234,
            "modificationTime": 3456,
            "permission": "read",
        },
    )
    assert stat.uri == URL("storage://default/user/path%23%252d%3f:@~%C3%9Fto")
    assert stat.uri.path == "/user/path#%2d?:@~ßto"
