import re
import sys
from pathlib import Path

from yarl import URL


def uri_from_cli(path_or_uri: str, username: str) -> URL:
    uri = URL(path_or_uri)
    # len(uri.scheme) == 1 is a workaround for Windows path like C:/path/to.txt
    if not uri.scheme or len(uri.scheme) == 1:
        # Workaround for urllib.parse.urlsplit()'s strange behavior with
        # URLs like "scheme:123".
        if re.fullmatch(r"[a-zA-Z0-9+\-.]{2,}:[0-9]+", path_or_uri):
            uri = URL(f"{path_or_uri}#")
        elif re.fullmatch(r"[0-9]+", path_or_uri):
            uri = URL(f"file:{path_or_uri}#")
        else:
            uri = URL(f"file:{path_or_uri}")
    if uri.scheme == "file":
        uri = normalize_local_path_uri(uri)
    elif uri.scheme == "storage":
        uri = normalize_storage_path_uri(uri, username)
    return uri


def normalize_storage_path_uri(uri: URL, username: str) -> URL:
    """Normalize storage url."""
    if uri.scheme != "storage":
        raise ValueError(
            f"Invalid storage scheme '{uri.scheme}://' "
            "(only 'storage://' is allowed)"
        )

    if uri.host == "~":
        uri = uri.with_host(username)
    elif not uri.host:
        uri = URL("storage://" + username + "/" + uri.path)
    uri = uri.with_path(uri.path.lstrip("/"))

    if "~" in uri.path:
        raise ValueError(f"Cannot expand user for {uri}")

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
    path = path.expanduser().absolute()
    ret = URL(path.as_uri())
    if "~" in ret.path:
        raise ValueError(f"Cannot expand user for {uri}")
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
