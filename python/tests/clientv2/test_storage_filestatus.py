from neuromation.clientv2 import FileStatus, FileStatusType


def test_from_api():
    stat = FileStatus.from_api(
        {
            "path": "path/to",
            "type": "FILE",
            "length": 1234,
            "modificationTime": 3456,
            "permission": "read",
        }
    )
    assert stat.path == "path/to"
    assert stat.type == FileStatusType.FILE
    assert stat.size == 1234
    assert stat.modification_time == 3456
    assert stat.permission == "read"


def test_file():
    stat = FileStatus.from_api(
        {
            "path": "path/to",
            "type": "FILE",
            "length": 1234,
            "modificationTime": 3456,
            "permission": "read",
        }
    )
    assert stat.type == FileStatusType.FILE
    assert stat.is_file()
    assert not stat.is_dir()


def test_is_dir():
    stat = FileStatus.from_api(
        {
            "path": "path/to",
            "type": "DIRECTORY",
            "length": 1234,
            "modificationTime": 3456,
            "permission": "read",
        }
    )
    assert stat.type == FileStatusType.DIRECTORY
    assert not stat.is_file()
    assert stat.is_dir()


def test_name():
    stat = FileStatus.from_api(
        {
            "path": "path/to",
            "type": "FILE",
            "length": 1234,
            "modificationTime": 3456,
            "permission": "read",
        }
    )
    assert stat.name == "to"
