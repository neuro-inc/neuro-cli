from neuromation.api import FileStatusType
from neuromation.api.storage import _file_status_from_api


def test_from_api() -> None:
    stat = _file_status_from_api(
        {
            "path": "name",
            "type": "FILE",
            "length": 1234,
            "modificationTime": 3456,
            "permission": "read",
        }
    )
    assert stat.path == "name"
    assert stat.type == FileStatusType.FILE
    assert stat.size == 1234
    assert stat.modification_time == 3456
    assert stat.permission == "read"


def test_file() -> None:
    stat = _file_status_from_api(
        {
            "path": "name",
            "type": "FILE",
            "length": 1234,
            "modificationTime": 3456,
            "permission": "read",
        }
    )
    assert stat.type == FileStatusType.FILE
    assert stat.is_file()
    assert not stat.is_dir()


def test_is_dir() -> None:
    stat = _file_status_from_api(
        {
            "path": "name",
            "type": "DIRECTORY",
            "length": 1234,
            "modificationTime": 3456,
            "permission": "read",
        }
    )
    assert stat.type == FileStatusType.DIRECTORY
    assert not stat.is_file()
    assert stat.is_dir()


def test_name() -> None:
    stat = _file_status_from_api(
        {
            "path": "name",
            "type": "FILE",
            "length": 1234,
            "modificationTime": 3456,
            "permission": "read",
        }
    )
    assert stat.name == "name"
