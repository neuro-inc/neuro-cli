import re
import sys
from pathlib import Path

from yarl import URL


def normalize_storage_path_uri(uri: URL, username: str) -> URL:
    """Normalize storage url."""
    if uri.scheme != "storage":
        raise ValueError(
            f"Invalid storage scheme '{uri.scheme}://' "
            "(only 'storage://' is allowed)"
        )

    if not uri.host:
        if uri.path.startswith("~"):
            raise ValueError(f"Cannot expand user for {uri}")
        uri = URL("storage://" + username + "/" + uri.path)
    elif uri.host == "~":
        uri = uri.with_host(username)
    elif uri.host.startswith("~"):  # type: ignore
        raise ValueError(f"Cannot expand user for {uri}")
    uri = uri.with_path(uri.path.lstrip("/"))

    return uri


def normalize_local_path_uri(uri: URL) -> URL:
    """Normalize local file url."""
    if uri.scheme != "file":
        raise ValueError(
            f"Invalid local file scheme '{uri.scheme}://' "
            "(only 'file://' is allowed)"
        )
    if uri.host:
        raise ValueError(f"Host part is not allowed, found '{uri.host}'")
    path = _extract_path(uri)
    path = path.expanduser()
    if str(path.parents[0]).startswith("~"):
        raise ValueError(f"Cannot expand user for {uri}")
    path = path.absolute()
    ret = URL(path.as_uri())
    while ret.path.startswith("//"):
        ret = ret.with_path(ret.path[1:])
    return ret


def _extract_path(uri: URL) -> Path:
    path = Path(uri.path)
    if sys.platform == "win32":
        # result of previous normalization
        if re.match(r"^[/\\][A-Za-z]:[/\\]", str(path)):
            return Path(str(path)[1:])
    return path
